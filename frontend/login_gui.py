import tkinter as tk
from tkinter import ttk, messagebox
import requests
from dashboard import Dashboard  # Import the Dashboard class

class LoginGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Login - Hotel Management System")
        self.root.geometry("400x300")
        
        self.api_base_url = "http://127.0.0.1:8000"  # Adjust this for your API
        
        self.setup_ui()

    def setup_ui(self):
        title_label = ttk.Label(self.root, text="Login", font=("Helvetica", 18))
        title_label.pack(pady=20)

        username_label = ttk.Label(self.root, text="Username:")
        username_label.pack(anchor=tk.W, padx=20)
        self.username_entry = ttk.Entry(self.root, width=30)
        self.username_entry.pack(padx=20, pady=5)

        password_label = ttk.Label(self.root, text="Password:")
        password_label.pack(anchor=tk.W, padx=20)
        self.password_entry = ttk.Entry(self.root, width=30, show="*")
        self.password_entry.pack(padx=20, pady=5)

        login_button = ttk.Button(self.root, text="Login", command=self.login)
        login_button.pack(pady=20)

        register_button = ttk.Button(self.root, text="Register", command=self.show_register_window)
        register_button.pack(pady=5)

    def login(self):
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
        self.register_window = tk.Toplevel(self.root)
        self.register_window.title("Register - Hotel Management System")
        self.register_window.geometry("400x400")
        self.setup_register_ui()

    def setup_register_ui(self):
        title_label = ttk.Label(self.register_window, text="Register", font=("Helvetica", 18))
        title_label.pack(pady=20)

        username_label = ttk.Label(self.register_window, text="Username:")
        username_label.pack(anchor=tk.W, padx=20)
        self.reg_username_entry = ttk.Entry(self.register_window, width=30)
        self.reg_username_entry.pack(padx=20, pady=5)

        password_label = ttk.Label(self.register_window, text="Password:")
        password_label.pack(anchor=tk.W, padx=20)
        self.reg_password_entry = ttk.Entry(self.register_window, width=30, show="*")
        self.reg_password_entry.pack(padx=20, pady=5)

        role_label = ttk.Label(self.register_window, text="Role:")
        role_label.pack(anchor=tk.W, padx=20)
        self.role_combobox = ttk.Combobox(self.register_window, values=["user", "admin"], state="readonly")
        self.role_combobox.pack(padx=20, pady=5)
        self.role_combobox.current(0)
        self.role_combobox.bind("<<ComboboxSelected>>", self.toggle_admin_password)

        self.reg_admin_password_label = ttk.Label(self.register_window, text="Admin Password:")
        self.reg_admin_password_label.pack(anchor=tk.W, padx=20)
        self.reg_admin_password_entry = ttk.Entry(self.register_window, width=30, show="*")
        self.reg_admin_password_entry.pack(padx=20, pady=5)
        self.reg_admin_password_label.pack_forget()
        self.reg_admin_password_entry.pack_forget()

        register_button = ttk.Button(self.register_window, text="Register", command=self.register)
        register_button.pack(pady=20)

    def toggle_admin_password(self, event):
        if self.role_combobox.get() == "admin":
            self.reg_admin_password_label.pack(anchor=tk.W, padx=20)
            self.reg_admin_password_entry.pack(padx=20, pady=5)
        else:
            self.reg_admin_password_label.pack_forget()
            self.reg_admin_password_entry.pack_forget()

    def register(self):
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
