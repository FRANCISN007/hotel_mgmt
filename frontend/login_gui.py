import tkinter as tk
from tkinter import ttk, messagebox
import requests
from dashboard import Dashboard  # Import the Dashboard class

class LoginGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Login - Hotel Management System")
        self.root.geometry("400x350")
        self.root.configure(bg="#f0f0f0")  # Light gray background

        # ✅ Store API Base URL
        self.api_base_url = "http://127.0.0.1:8000"  # Adjust for your API

        self.setup_ui()

    def setup_ui(self):
        """Sets up the login UI with better design."""
        frame = tk.Frame(self.root, bg="white", padx=20, pady=20, relief="raised", bd=2)
        frame.pack(pady=40, padx=20)

        title_label = tk.Label(frame, text="Login", font=("Arial", 18, "bold"), bg="white")
        title_label.pack(pady=10)

        username_label = tk.Label(frame, text="Username:", font=("Arial", 12), bg="white")
        username_label.pack(anchor="w")
        self.username_entry = ttk.Entry(frame, width=30)
        self.username_entry.pack(pady=5)

        password_label = tk.Label(frame, text="Password:", font=("Arial", 12), bg="white")
        password_label.pack(anchor="w")
        self.password_entry = ttk.Entry(frame, width=30, show="*")
        self.password_entry.pack(pady=5)

        login_button = ttk.Button(frame, text="Login", command=self.login)
        login_button.pack(pady=10)

        register_button = tk.Button(frame, text="Register", command=self.show_register_window, fg="blue", borderwidth=0, bg="white", font=("Arial", 10, "underline"))
        register_button.pack()

    def login(self):
        """Handles login functionality."""
        username = self.username_entry.get()
        password = self.password_entry.get()

        if not username or not password:
            messagebox.showerror("Error", "Please enter both username and password.")
            return

        try:
            response = requests.post(f"{self.api_base_url}/users/token", data={"username": username, "password": password})
            
            if response.status_code == 500:
                messagebox.showerror("Error", "Invalid username or password.")
                return

            response.raise_for_status()
            data = response.json()
            token = data.get("access_token")

            if token:
                messagebox.showinfo("Success", "Login successful!")
                self.root.destroy()
                dashboard_root = tk.Tk()
                Dashboard(dashboard_root, token)
                dashboard_root.mainloop()
            else:
                messagebox.showerror("Error", "Invalid response from server.")
        except requests.RequestException as e:
            messagebox.showerror("Error", f"Login failed: {e}")

    def show_register_window(self):
        """Opens the registration window."""
        self.register_window = tk.Toplevel(self.root)
        self.register_window.title("Register - Hotel Management System")
        self.register_window.geometry("400x450")
        self.register_window.configure(bg="#f0f0f0")

        self.setup_register_ui()

    def setup_register_ui(self):
        """Sets up the registration UI with better styling."""
        frame = tk.Frame(self.register_window, bg="white", padx=20, pady=20, relief="raised", bd=2)
        frame.pack(pady=30, padx=20)

        title_label = tk.Label(frame, text="Register", font=("Arial", 18, "bold"), bg="white")
        title_label.pack(pady=10)

        username_label = tk.Label(frame, text="Username:", font=("Arial", 12), bg="white")
        username_label.pack(anchor="w")
        self.reg_username_entry = ttk.Entry(frame, width=30)
        self.reg_username_entry.pack(pady=5)

        password_label = tk.Label(frame, text="Password:", font=("Arial", 12), bg="white")
        password_label.pack(anchor="w")
        self.reg_password_entry = ttk.Entry(frame, width=30, show="*")
        self.reg_password_entry.pack(pady=5)

        role_label = tk.Label(frame, text="Role:", font=("Arial", 12), bg="white")
        role_label.pack(anchor="w")
        self.role_combobox = ttk.Combobox(frame, values=["user", "admin"], state="readonly")
        self.role_combobox.pack(pady=5)
        self.role_combobox.current(0)
        self.role_combobox.bind("<<ComboboxSelected>>", self.toggle_admin_password)

        # Admin Password (Hidden by default)
        self.reg_admin_password_label = tk.Label(frame, text="Admin Password:", font=("Arial", 12), bg="white")
        self.reg_admin_password_entry = ttk.Entry(frame, width=30, show="*")

        # Register Button
        register_button = ttk.Button(frame, text="Register", command=self.register)
        register_button.pack(pady=15)

    def toggle_admin_password(self, event):
        """Shows/hides the admin password field based on role selection."""
        if self.role_combobox.get() == "admin":
            self.reg_admin_password_label.pack(anchor="w")
            self.reg_admin_password_entry.pack(pady=5)
        else:
            self.reg_admin_password_label.pack_forget()
            self.reg_admin_password_entry.pack_forget()

    def register(self):
        """Handles user registration."""
        username = self.reg_username_entry.get()
        password = self.reg_password_entry.get()
        role = self.role_combobox.get()
        admin_password = self.reg_admin_password_entry.get() if role == "admin" else None

        if not username or not password:
            messagebox.showerror("Error", "Please enter both username and password.")
            return

        try:
            # ✅ Use self.api_base_url from LoginGUI
            data = {"username": username, "password": password, "role": role, "admin_password": admin_password}
            response = requests.post(f"{self.api_base_url}/users/register/", json=data)  # FIXED ✅
            
            if response.status_code == 400:
                messagebox.showerror("Error", "Username already exists.")
                return
            
            response.raise_for_status()
            messagebox.showinfo("Success", "User registered successfully!")
            self.register_window.destroy()
        except requests.RequestException as e:
            messagebox.showerror("Error", f"Registration failed: {e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = LoginGUI(root)
    root.mainloop()
