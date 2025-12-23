import os
import sys
import shutil
import subprocess
import tempfile
import asyncio
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("PIOManager")

class PlatformIOManager:
    def __init__(self, base_path: Optional[str] = None):
        if base_path:
            self.base_path = Path(base_path).resolve()
        else:
            # Detect whether running as script or frozen exe
            if getattr(sys, 'frozen', False):
                self.base_path = Path(sys._MEIPASS) # Only works if pio is bundled in temp, which is hard. 
                # Better: assume exe is in a folder (dist or final install) and look relative to executable
                self.base_path = Path(sys.executable).parent
            else:
                self.base_path = Path(__file__).parent.resolve()

        self.portable_core_dir = self.base_path / "portable_pio"
        self.vendor_lib_dir = self.base_path / "vendor" / "libraries"
        self.drivers_dir = self.base_path / "resources" / "drivers"

        # Environment variables to force portability
        self.env = os.environ.copy()
        self.env["PLATFORMIO_CORE_DIR"] = str(self.portable_core_dir)
        self.env["PLATFORMIO_GLOBAL_LIB_DIR"] = str(self.vendor_lib_dir)
        # Disable internet usage for package resolution if possible, though PIO might still try check updates.
        # "PLATFORMIO_OFFLINE": "1" is not a standard flag but we can try to rely on pre-installed data.

    def _get_pio_command(self) -> List[str]:
        """
        Returns the command prefix to run PIO.
        Ideally uses the bundled python environment if frozen.
        """
        # If we are running in a frozen app, we might need to rely on a 'pio' executable bundled
        # OR run `subprocess.run([sys.executable, "-m", "platformio", ...])` if platformio is installed in the internal python env.
        # For this implementation, we assume `python -m platformio` works with the current interpreter.
        return [sys.executable, "-m", "platformio"]

    def check_environment(self) -> bool:
        """Checks if the portable environment is ready."""
        if not self.portable_core_dir.exists():
            logger.error(f"Portable Core not found at {self.portable_core_dir}")
            return False
            
        # Check for drivers folder (just warning if missing)
        if not self.drivers_dir.exists():
            logger.warning(f"Drivers directory not found at {self.drivers_dir}")

        return True

    def generate_ini(self, project_dir: Path, board_config: Dict[str, Any], sensor_libs: List[str]):
        """Creates the platformio.ini file."""
        ini_path = project_dir / "platformio.ini"
        
        # Build lib_deps string
        # We assume libraries are folders in vendor/libraries, so we just list their names 
        # provided PIO can resolve them from custom lib_extra_dirs.
        # However, for offline usage with lib_extra_dirs, we just need the name.
        lib_deps_str = "\n    ".join(sensor_libs)

        content = f"""
[env:{board_config['board_id']}]
platform = {board_config['platform']}
board = {board_config['board_id']}
framework = {board_config['framework']}
monitor_speed = 115200
upload_protocol = {board_config.get('upload_protocol', 'esptool')}

; Point to local offline libraries
lib_extra_dirs = {self.vendor_lib_dir.resolve()}

lib_deps =
    {lib_deps_str}
"""
        with open(ini_path, "w") as f:
            f.write(content)

    async def build_and_upload(self, code: str, board_config: Dict[str, Any], port: str, sensor_libs: List[str], log_callback):
        """
        Async generator or callback-based method to run the build/upload.
        """
        if not self.check_environment():
            await log_callback({"type": "error", "message": "Portable environment not found! Run prepare_portable.py or reinstall."})
            return

        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            src_path = project_path / "src"
            src_path.mkdir()

            # Write Code
            with open(src_path / "main.cpp", "w") as f:
                f.write(code)

            # Generate INI
            self.generate_ini(project_path, board_config, sensor_libs)

            cmd = self._get_pio_command() + ["run", "--target", "upload", "--upload-port", port]
            
            await log_callback({"type": "log", "message": f"Starting build for {board_config['board_id']} on {port}..."})
            await log_callback({"type": "log", "message": f"Project Directory: {project_path}"})
            
            # Start Subprocess
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=str(project_path),
                env=self.env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            # Stream output
            async def read_stream(stream, is_stderr=False):
                while True:
                    line = await stream.readline()
                    if not line:
                        break
                    decoded = line.decode('utf-8', errors='replace').strip()
                    if decoded:
                        msg_type = "error" if "error" in decoded.lower() and not "compiling" in decoded.lower() else "log"
                        # Simple keyword heuristic for color coding in UI
                        if "success" in decoded.lower(): msg_type = "success"
                        elif "uploading" in decoded.lower(): msg_type = "upload"
                        
                        await log_callback({"type": "log", "message": decoded, "category": msg_type})

            await asyncio.gather(
                read_stream(process.stdout),
                read_stream(process.stderr, is_stderr=True)
            )

            await process.wait()

            if process.returncode == 0:
                await log_callback({"type": "success", "message": "Upload Complete!"})
            else:
                await log_callback({"type": "error", "message": f"Process failed with code {process.returncode}"})

    def list_ports(self):
        import serial.tools.list_ports
        return [p.device for p in serial.tools.list_ports.comports()]

    def install_driver(self, driver_name: str):
        """
        Launches the installer for the specified driver.
        Expected driver_name: 'CH340', 'CP210x'
        """
        driver_map = {
            "CH340": "CH34x_Install_Windows_v3_4.exe",
            "CP210x": "CP210xVCPInstaller_x64.exe",
            "Arduino": "arduino-usb-drivers.exe" # hypothetical name
        }
        
        exe_name = driver_map.get(driver_name)
        if not exe_name:
            return False, "Driver not found in map"

        installer_path = self.drivers_dir / exe_name
        
        if not installer_path.exists():
             return False, f"Installer not found at {installer_path}"

        try:
            # Need to run as admin. 'runas' verb in ShellExecute might work but python's os.startfile doesn't support verbs easily.
            # Using subprocess with shell=True might rely on installer asking for elevation.
            subprocess.Popen([str(installer_path)], shell=True)
            return True, "Installer launched"
        except Exception as e:
            return False, str(e)
