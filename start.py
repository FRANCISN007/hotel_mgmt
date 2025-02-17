import subprocess
import time
import threading
import sys
import os

# -*- coding: utf-8 -*-


# Function to start the FastAPI backend
def start_backend():
    with open("backend_log.txt", "w") as log_file:
        process = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000", "--reload"],
            stdout=log_file,
            stderr=log_file,
        )
    process.wait()

# Function to check if backend is running
def is_backend_running():
    import requests
    for attempt in range(20):  # Check for 20 seconds
        try:
            response = requests.get("http://127.0.0.1:8000/docs")
            if response.status_code == 200:
                return True
        except requests.ConnectionError:
            time.sleep(1)
    return False

# Function to start the Tkinter frontend
def start_frontend():
    frontend_path = os.path.join(os.getcwd(), "frontend", "main.py")
    subprocess.run([sys.executable, frontend_path])

# Start backend in a separate thread
backend_thread = threading.Thread(target=start_backend, daemon=True)
backend_thread.start()

# Ensure backend is running before launching frontend
if is_backend_running():
    print(" Backend is running, launching frontend...")
    start_frontend()
else:
    print(" Backend failed to start. Check backend_log.txt for errors.")
