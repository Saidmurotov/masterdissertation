import PyInstaller.__main__
import os
import shutil

def build():
    print("Starting PyInstaller build...")
    
    # Define templates directory
    templates_dir = os.path.join(os.getcwd(), "templates")
    
    # Clean previous build
    if os.path.exists("dist"):
        shutil.rmtree("dist")
    if os.path.exists("build"):
        shutil.rmtree("build")

    # PyInstaller arguments
    args = [
        "server_entry.py",
        "--name=backend_server",
        "--onefile",
        "--clean",
        # Add templates directory to the bundle
        f"--add-data={templates_dir};templates",
        # Hidden imports often missed by PyInstaller analysis
        "--hidden-import=uvicorn.logging",
        "--hidden-import=uvicorn.loops",
        "--hidden-import=uvicorn.loops.auto",
        "--hidden-import=uvicorn.protocols",
        "--hidden-import=uvicorn.protocols.http",
        "--hidden-import=uvicorn.protocols.http.auto",
        "--hidden-import=uvicorn.lifespan",
        "--hidden-import=uvicorn.lifespan.on",
        "--hidden-import=engineio.async_drivers.asgi",
        "--hidden-import=socketio",
        "--log-level=INFO"
    ]

    PyInstaller.__main__.run(args)
    print("Build complete. Executable is in 'dist/backend_server.exe'.")

if __name__ == "__main__":
    build()
