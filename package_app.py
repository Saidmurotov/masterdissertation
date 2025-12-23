import os
import shutil
import time

DIST_DIR = "DAQ_System_Final"
BACKEND_SRC = "dist/backend_server.exe"
TEMPLATES_SRC = "templates"

def package():
    if os.path.exists(DIST_DIR):
        shutil.rmtree(DIST_DIR)
    os.makedirs(DIST_DIR)
    
    print(f"Created {DIST_DIR}...")
    
    # Check if backend exists
    if not os.path.exists(BACKEND_SRC):
        print("Backend executable not found in dist/. Please run build_backend.py first.")
        return

    # Copy Backend
    shutil.copy(BACKEND_SRC, os.path.join(DIST_DIR, "backend_server.exe"))
    print("Copied backend server.")

    # Copy Templates (Optional: PyInstaller bundles them, but putting them outside allows user editing if configured to look there)
    # The previous plan said "Bundle inside the EXE or place here". 
    # Since we used --add-data, they are inside. But providing them externally is nice for reference or if code logic prefers it.
    # Our daq_config.py logic prioritizes _MEIPASS, so external templates won't be used unless we change logic.
    # However, request asked for "templates/ (Bundle inside ... OR place here)". 
    # We will copy them for completeness as per folder structure request.
    shutil.copytree(TEMPLATES_SRC, os.path.join(DIST_DIR, "templates"))
    print("Copied templates.")

    # Create dummy config.json
    with open(os.path.join(DIST_DIR, "config.json"), "w") as f:
        f.write('{"mqtt_broker": "localhost", "theme": "dark"}')
    print("Created default config.json.")
    
    # Create Dummy PDF
    with open(os.path.join(DIST_DIR, "README.pdf"), "w") as f:
        f.write("%PDF-1.4 ... (Mock PDF Content)")
    print("Created README.pdf placeholder.")
    
    print("\npackaging complete!")
    print(f"Please build the Flutter App ('flutter build windows') and copy the contents of 'build/windows/x64/runner/Release/' into '{DIST_DIR}'.")
    print(f"Rename 'daq_sensor_dashboard.exe' to 'DAQ_Intelligent_App.exe'.")

if __name__ == "__main__":
    package()
