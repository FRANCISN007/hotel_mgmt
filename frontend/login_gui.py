#login and registration
import tkinter as tk
from tkinter import ttk, messagebox
import requests
from dashboard import Dashboard  # Import the Dashboard class



# Login and Registration Window
class LoginGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Login - Hotel Management System")
        self.root.geometry("400x300")

        # Base API URL
        self.api_base_url = "http://127.0.0.1:8000"  # Adjusted to match your FastAPI base URL

        # UI Components
        self.setup_ui()

    def setup_ui(self):
        # Title Label
        title_label = ttk.Label(self.root, text="Login", font=("Helvetica", 18))
        title_label.pack(pady=20)

        # Username Entry
        username_label = ttk.Label(self.root, text="Username:")
        username_label.pack(anchor=tk.W, padx=20)
        self.username_entry = ttk.Entry(self.root, width=30)
        self.username_entry.pack(padx=20, pady=5)

        # Password Entry
        password_label = ttk.Label(self.root, text="Password:")
        password_label.pack(anchor=tk.W, padx=20)
        self.password_entry = ttk.Entry(self.root, width=30, show="*")
        self.password_entry.pack(padx=20, pady=5)

        # Login Button
        login_button = ttk.Button(self.root, text="Login", command=self.login)
        login_button.pack(pady=20)

        # Register Button
        register_button = ttk.Button(self.root, text="Register", command=self.show_register_window)
        register_button.pack(pady=5)

    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()

        if not username or not password:
            messagebox.showerror("Error", "Please enter both username and password.")
            return

        try:
            # Make API request for token
            response = requests.post(
                f"{self.api_base_url}/users/token",
                data={"username": username, "password": password}
            )

            # Check for status code and handle different errors
            if response.status_code == 500:  # Unauthorized, meaning invalid username or password
                try:
                    error_detail = response.json().get("detail", "Invalid username or password.")
                except ValueError:
                    error_detail = "Invalid username or password."  # Fallback to generic message if JSON parsing fails

                messagebox.showerror("Error", error_detail)
                return

            # Check for other potential response errors (like 4xx, 5xx)
            response.raise_for_status()

            # Parse token from response
            data = response.json()
            token = data.get("access_token")
            if token:
                messagebox.showinfo("Success", "Login successful!")
                self.root.destroy()  # Close the login window
                # Open Dashboard window
                dashboard_root = tk.Tk()
                Dashboard(dashboard_root, token)
                dashboard_root.mainloop()
            else:
                messagebox.showerror("Error", "Invalid response from server.")

        except requests.RequestException as e:
            # Catch other types of errors (e.g., network issues, server errors)
            messagebox.showerror("Error", f"Login failed: {e}")

    def show_register_window(self):
        self.register_window = tk.Toplevel(self.root)
        self.register_window.title("Register - Hotel Management System")
        self.register_window.geometry("400x350")

        # Register UI Components
        self.setup_register_ui()

    def setup_register_ui(self):
        # Title Label
        title_label = ttk.Label(self.register_window, text="Register", font=("Helvetica", 18))
        title_label.pack(pady=20)

        # Username Entry
        username_label = ttk.Label(self.register_window, text="Username:")
        username_label.pack(anchor=tk.W, padx=20)
        self.reg_username_entry = ttk.Entry(self.register_window, width=30)
        self.reg_username_entry.pack(padx=20, pady=5)

        # Password Entry
        password_label = ttk.Label(self.register_window, text="Password:")
        password_label.pack(anchor=tk.W, padx=20)
        self.reg_password_entry = ttk.Entry(self.register_window, width=30, show="*")
        self.reg_password_entry.pack(padx=20, pady=5)

        # Admin Password (if applicable)
        self.reg_admin_password_label = ttk.Label(self.register_window, text="Admin Password (if registering as admin):")
        self.reg_admin_password_label.pack(anchor=tk.W, padx=20)
        self.reg_admin_password_entry = ttk.Entry(self.register_window, width=30, show="*")
        self.reg_admin_password_entry.pack(padx=20, pady=5)

        # Register Button
        register_button = ttk.Button(self.register_window, text="Register", command=self.register)
        register_button.pack(pady=20)

    def register(self):
        username = self.reg_username_entry.get()
        password = self.reg_password_entry.get()
        admin_password = self.reg_admin_password_entry.get()

        if not username or not password:
            messagebox.showerror("Error", "Please enter both username and password.")
            return

        try:
            # Create the registration data
            data = {
                "username": username,
                "password": password,
                "role": "admin" if admin_password else "user",
                "admin_password": admin_password if admin_password else None
            }

            # Send the registration request to the backend
            response = requests.post(
                f"{self.api_base_url}/users/register/",
                json=data
            )

            # Check if the username already exists by inspecting the response
            if response.status_code == 400:
                messagebox.showerror("Error", "Username already exists.")
                return

            # Handle other response errors
            response.raise_for_status()

            messagebox.showinfo("Success", "User registered successfully!")
            self.register_window.destroy()  # Close the register window

        except requests.RequestException as e:
            messagebox.showerror("Error", f"Registration failed: {e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = LoginGUI(root)
    root.mainloop()
