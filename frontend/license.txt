import tkinter as tk
from tkinter import messagebox
import requests

API_URL = "http://localhost:8000/license"  # FastAPI server URL

# Function to generate a license key
def generate_license():
    license_password = password_entry.get()
    key = key_entry.get()
    
    if not license_password or not key:
        messagebox.showerror("Input Error", "Please enter both license password and key.")
        return
    
    try:
        response = requests.post(
            f"{API_URL}/generate",
            json={"license_password": license_password, "key": key},
        )
        response.raise_for_status()
        new_license = response.json()
        messagebox.showinfo("License Generated", f"New License Key: {new_license['key']}")
    except requests.exceptions.HTTPError as err:
        messagebox.showerror("Error", f"Error generating license: {err}")
    except Exception as e:
        messagebox.showerror("Error", f"An unexpected error occurred: {e}")

# Function to verify the license key
def verify_license():
    key = verify_key_entry.get()
    
    if not key:
        messagebox.showerror("Input Error", "Please enter a license key.")
        return
    
    try:
        response = requests.get(f"{API_URL}/verify/{key}")
        response.raise_for_status()
        result = response.json()
        if result["valid"]:
            messagebox.showinfo("License Valid", "The license key is valid!")
        else:
            messagebox.showwarning("Invalid License", result["message"])
    except requests.exceptions.HTTPError as err:
        messagebox.showerror("Error", f"Error verifying license: {err}")
    except Exception as e:
        messagebox.showerror("Error", f"An unexpected error occurred: {e}")

# Tkinter window setup
root = tk.Tk()
root.title("License Management")
root.geometry("400x300")

# Generate License Section
generate_frame = tk.LabelFrame(root, text="Generate License Key", padx=10, pady=10)
generate_frame.pack(padx=10, pady=10, fill="both", expand=True)

password_label = tk.Label(generate_frame, text="Admin License Password:")
password_label.pack(padx=5, pady=5)

password_entry = tk.Entry(generate_frame, show="*")
password_entry.pack(padx=5, pady=5)

key_label = tk.Label(generate_frame, text="License Key:")
key_label.pack(padx=5, pady=5)

key_entry = tk.Entry(generate_frame)
key_entry.pack(padx=5, pady=5)

generate_button = tk.Button(generate_frame, text="Generate License", command=generate_license)
generate_button.pack(pady=10)

# Verify License Section
verify_frame = tk.LabelFrame(root, text="Verify License Key", padx=10, pady=10)
verify_frame.pack(padx=10, pady=10, fill="both", expand=True)

verify_key_label = tk.Label(verify_frame, text="Enter License Key to Verify:")
verify_key_label.pack(padx=5, pady=5)

verify_key_entry = tk.Entry(verify_frame)
verify_key_entry.pack(padx=5, pady=5)

verify_button = tk.Button(verify_frame, text="Verify License", command=verify_license)
verify_button.pack(pady=10)

root.mainloop()
