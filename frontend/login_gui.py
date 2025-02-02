import tkinter as tk
from tkinter import ttk, messagebox
import requests
from dashboard import Dashboard  # Import the Dashboard class

class LoginGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Login - Hotel Management System")
        self.root.geometry("500x470")  # ✅ Increased height to fully show Register button
        self.root.configure(bg="#f0f0f0")  

        # ✅ API Base URL
        self.api_base_url = "http://127.0.0.1:8000"  

        self.setup_ui()

    def setup_ui(self):
        """Sets up the login UI."""
        frame = tk.Frame(self.root, bg="white", padx=30, pady=40, relief="raised", bd=3)  # ✅ Increased padding
        frame.pack(pady=30)

        title_label = tk.Label(frame, text="Login", font=("Arial", 20, "bold"), bg="white")
        title_label.pack(pady=15)

        username_label = tk.Label(frame, text="Username:", font=("Arial", 14), bg="white")
        username_label.pack(anchor="w")
        self.username_entry = ttk.Entry(frame, width=40)
        self.username_entry.pack(pady=6)

        password_label = tk.Label(frame, text="Password:", font=("Arial", 14), bg="white")
        password_label.pack(anchor="w")
        self.password_entry = ttk.Entry(frame, width=40, show="*")
        self.password_entry.pack(pady=8)

        login_button = ttk.Button(frame, text="Login", command=self.login)
        login_button.pack(pady=15, ipadx=20, ipady=5)  

        # ✅ Register Button (Fully Visible Below the Frame)
        register_button = tk.Button(self.root, text="Register", command=self.show_register_window, fg="blue", borderwidth=0, bg="#f0f0f0", font=("Arial", 12, "underline"))
        register_button.pack(pady=20)  # ✅ Increased padding

    def login(self):
        """Handles login."""
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
        self.register_window.geometry("500x520")  
        self.register_window.configure(bg="#f0f0f0")

        self.setup_register_ui()

    def setup_register_ui(self):
        """Sets up the registration UI."""
        frame = tk.Frame(self.register_window, bg="white", padx=30, pady=30, relief="raised", bd=3)
        frame.pack(expand=True, fill="both", padx=20, pady=20)  

        title_label = tk.Label(frame, text="Register", font=("Arial", 20, "bold"), bg="white")
        title_label.pack(pady=15)

        username_label = tk.Label(frame, text="Username:", font=("Arial", 14), bg="white")
        username_label.pack(anchor="w")
        self.reg_username_entry = ttk.Entry(frame, width=40)
        self.reg_username_entry.pack(pady=8)

        password_label = tk.Label(frame, text="Password:", font=("Arial", 14), bg="white")
        password_label.pack(anchor="w")
        self.reg_password_entry = ttk.Entry(frame, width=40, show="*")
        self.reg_password_entry.pack(pady=8)

        role_label = tk.Label(frame, text="Role:", font=("Arial", 14), bg="white")
        role_label.pack(anchor="w")
        self.role_combobox = ttk.Combobox(frame, values=["user", "admin"], state="readonly", font=("Arial", 12))
        self.role_combobox.pack(pady=8)
        self.role_combobox.current(0)
        self.role_combobox.bind("<<ComboboxSelected>>", self.toggle_admin_password)

        # Admin Password (Hidden by default)
        self.reg_admin_password_label = tk.Label(frame, text="Admin Password:", font=("Arial", 14), bg="white")
        self.reg_admin_password_entry = ttk.Entry(frame, width=40, show="*")

        # ✅ Ensuring Register Button is Visible
        register_button = ttk.Button(frame, text="Register", command=self.register)
        register_button.pack(pady=15, ipadx=20, ipady=5, anchor="center")  

    def toggle_admin_password(self, event):
        """Shows/hides the admin password field based on role selection."""
        if self.role_combobox.get() == "admin":
            self.reg_admin_password_label.pack(anchor="w", pady=5)
            self.reg_admin_password_entry.pack(pady=8)
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
            data = {"username": username, "password": password, "role": role, "admin_password": admin_password}
            response = requests.post(f"{self.api_base_url}/users/register/", json=data)  
            
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