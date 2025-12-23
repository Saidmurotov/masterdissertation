import multiprocessing
import uvicorn
import sys
import os

# Ensure we can import modules from the current directory
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main_api import app

def run_server():
    # Freeze support is needed for multiprocessing on Windows when frozen
    multiprocessing.freeze_support()
    
    # Run uvicorn programmatically
    # Host 127.0.0.1 is safer for a local app than 0.0.0.0
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")

if __name__ == "__main__":
    run_server()
