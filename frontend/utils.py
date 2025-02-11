import os
import requests
import pandas as pd
import subprocess
from tkinter import filedialog, messagebox

TOKEN_FILE = "token.txt"
API_BASE_URL = "http://127.0.0.1:8000"  # Update this if needed
BASE_URL = f"{API_BASE_URL}/bookings"  # For booking-related endpoints


def save_token(token):
    """Save the token to a file."""
    with open(TOKEN_FILE, "w") as file:
        file.write(token)

def load_token():
    """Load the token from the file."""
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "r") as file:
            return file.read().strip()
    return None


def get_user_role(token):
    url = "http://127.0.0.1:8000/users/me"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)

    try:
        user_data = response.json()
        print("User Data Response:", user_data)  # Debugging line

        if not isinstance(user_data, dict):  # Ensure it's a dictionary
            print("Unexpected response format:", user_data)
            return "guest"

        return user_data.get("role", "guest")  # Default to "guest"
    
    except Exception as e:
        print("Error fetching user role:", e)
        return "guest"  # Safe fallback

import requests

def api_request(endpoint, method="GET", data=None, token=None):
    url = f"http://127.0.0.1:8000{endpoint}"  # Ensure this is the correct API base URL
    headers = {"Authorization": f"Bearer {token}"} if token else {}

    try:
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            response = requests.post(url, json=data, headers=headers)
        elif method == "PUT":
            response = requests.put(url, json=data, headers=headers)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers)
        else:
            return None

        if response.status_code == 200:
            return response.json()  # Ensure correct JSON handling
        else:
            print(f"Error: {response.status_code}, Response: {response.text}")  # Print error details
            return None
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        return None

import requests

def perform_booking_action(endpoint, data, token):
    """ Perform API requests for booking management """
    url = f"http://127.0.0.1:8000/bookings/{endpoint}"  # Adjust base URL if needed
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    try:
        response = requests.post(url, json=data, headers=headers)  # Change method if necessary
        return response.json()
    except Exception as e:
        return {"error": str(e)}
    
def export_to_excel(data, default_filename="report.xlsx"):
    """Export data (list of dictionaries) to an Excel file."""
    if not data:
        messagebox.showwarning("No Data", "No data available to export.")
        return

    file_path = filedialog.asksaveasfilename(
        defaultextension=".xlsx",
        filetypes=[("Excel Files", "*.xlsx"), ("All Files", "*.*")],
        title="Save Report As",
        initialfile=default_filename
    )

    if not file_path:
        return  # User canceled

    try:
        df = pd.DataFrame(data)
        df.to_excel(file_path, index=False)
        messagebox.showinfo("Success", f"Report saved as {file_path}")
        return file_path

    except Exception as e:
        messagebox.showerror("Error", f"Failed to export: {str(e)}")
        return None

def print_excel(file_path):
    """Open and print an Excel file."""
    if not os.path.exists(file_path):
        messagebox.showerror("Error", "File not found!")
        return

    try:
        os.startfile(file_path, "print")  # Windows
        # subprocess.run(["lp", file_path])  # Mac/Linux alternative
        messagebox.showinfo("Printing", "Report is being printed.")

    except Exception as e:
        messagebox.showerror("Error", f"Failed to print: {str(e)}")
    
   