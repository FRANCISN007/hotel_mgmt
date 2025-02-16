import subprocess
import time
import threading
import sys
import os

# Function to start the FastAPI backend
def start_backend():
    backend_path = os.path.join(os.getcwd(), "app", "main.py")

    # Open backend process and log output for debugging
    with open("backend_log.txt", "w") as log_file:
        process = subprocess.Popen(
            [sys.executable, backend_path],
            stdout=log_file,
            stderr=log_file,
        )
    
    # Wait for the process to complete (should run indefinitely)
    process.wait()

# Function to check if backend is running
def is_backend_running():
    time.sleep(3)  # Wait a bit before checking
    return True  # Ideally, implement a real check (like an HTTP request to FastAPI)

# Function to start the Tkinter frontend
def start_frontend():
    frontend_path = os.path.join(os.getcwd(), "frontend", "main.py")
    subprocess.run([sys.executable, frontend_path])

# Start backend in a separate thread
backend_thread = threading.Thread(target=start_backend, daemon=True)
backend_thread.start()

# Ensure backend is running before launching frontend
while not is_backend_running():
    time.sleep(1)  # Keep checking if backend is ready

# Start frontend
start_frontend()
