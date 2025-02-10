import tkinter as tk
from tkinter import messagebox
import requests
from login_gui import LoginGUI

API_URL = "http://localhost:8000/license"  # FastAPI server URL

class LicenseGUI(tk.Frame):  # Inherit from tk.Frame
    def __init__(self, master, show_login_screen_callback):
        super().__init__(master)  # Initialize the parent class (tk.Frame)
        self.master = master
        self.show_login_screen_callback = show_login_screen_callback  # Save the callback
        self.pack()  # This will pack the frame to the root window
        self.master.title("License Management")
        self.master.geometry("500x400")  # Increase window size for better layout
        
        # Generate License Section
        self.generate_frame = tk.LabelFrame(self, text="Generate License Key", padx=10, pady=10)
        self.generate_frame.pack(padx=10, pady=10, fill="both", expand=True)

        self.password_label = tk.Label(self.generate_frame, text="Admin License Password:")
        self.password_label.pack(padx=5, pady=5)

        self.password_entry = tk.Entry(self.generate_frame, show="*", width=30)  # Increase width for better visibility
        self.password_entry.pack(padx=5, pady=5)

        self.key_label = tk.Label(self.generate_frame, text="License Key:")
        self.key_label.pack(padx=5, pady=5)

        self.key_entry = tk.Entry(self.generate_frame, width=30)  # Increase width for better visibility
        self.key_entry.pack(padx=5, pady=5)

        self.generate_button = tk.Button(self.generate_frame, text="Generate License", command=self.generate_license)
        self.generate_button.pack(pady=10)

        # Verify License Section
        self.verify_frame = tk.LabelFrame(self, text="Verify License Key", padx=10, pady=10)
        self.verify_frame.pack(padx=10, pady=10, fill="both", expand=True)

        self.verify_key_label = tk.Label(self.verify_frame, text="Enter License Key to Verify:")
        self.verify_key_label.pack(padx=5, pady=5)

        self.verify_key_entry = tk.Entry(self.verify_frame, width=30)  # Increase width for better visibility
        self.verify_key_entry.pack(padx=5, pady=5)

        self.verify_button = tk.Button(self.verify_frame, text="Verify License", command=self.verify_license)
        self.verify_button.pack(pady=10)


    # Function to generate a license key
    def generate_license(self):
        license_password = self.password_entry.get()
        key = self.key_entry.get()

        if not license_password or not key:
            messagebox.showerror("Input Error", "Please enter both license password and key.")
            return

        try:
            # Debugging: print the payload to verify the data
            

            # Modify the request to send data as query parameters
            response = requests.post(
                f"{API_URL}/generate?license_password={license_password}&key={key}", 
                headers={"Content-Type": "application/json"}  # Set content-type as JSON
            )

            # Check for response status code to debug error
            #print(f"Response status: {response.status_code}")
            #rint(f"Response body: {response.text}")

            response.raise_for_status()  # Check if the request was successful (status code 200)
            new_license = response.json()  # Parse the response JSON

            messagebox.showinfo("License Generated", f"New License Key: {new_license['key']}")

        except requests.exceptions.HTTPError as err:
        # ✅ Check for incorrect password response
            if response.status_code == 401:  # Assuming 401 is returned for wrong password
                messagebox.showerror("Error", "Wrong password entered.")
            else:
                messagebox.showerror("Error", "Wrong password entered.")

        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred: {e}")

    # Function to verify the license key
    def verify_license(self):
        key = self.verify_key_entry.get()

        if not key:
            messagebox.showerror("Input Error", "Please enter a license key.")
            return

        try:
            response = requests.get(f"{API_URL}/verify/{key}")
            response.raise_for_status()
            result = response.json()

            if result["valid"]:
                messagebox.showinfo("License Valid", "The license key is valid!")

                # Close the license window
                self.master.withdraw()  # Hides the license window instead of destroying it

                # Create a new window for login
                login_window = tk.Toplevel(self.master)
                LoginGUI(login_window)

            else:
                messagebox.showwarning("Invalid License", result["message"])

        except requests.exceptions.HTTPError as err:
            messagebox.showerror("Error","Invalid license key")
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred: {e}")


# Function to transition to the login screen
def show_login_screen():
    # Clear the current window and transition to the login screen
    for widget in root.winfo_children():
        widget.destroy()

    from login_gui import LoginGUI  # Import LoginGUI and show it
    login_gui = LoginGUI(root)
    login_gui.pack()


# Tkinter window setup
root = tk.Tk()
root.title("License Management")
root.geometry("500x400")  # Increase window size for better layout

# Create License GUI window
license_screen = LicenseGUI(root, show_login_screen)
root.mainloop()
