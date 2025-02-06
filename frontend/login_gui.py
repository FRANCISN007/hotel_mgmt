import tkinter as tk
from tkinter import ttk, messagebox
import requests
from dashboard import Dashboard  # Import the Dashboard class

class LoginGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Login - Hotel Management System")
        self.root.geometry("700x500")  # Set initial size
        self.root.state("zoomed")  # ✅ Full-screen (Zoomed)
        
        # ✅ Create a full gray background using Canvas
        self.canvas = tk.Canvas(self.root, bg="#D3D3D3")
        self.canvas.pack(fill="both", expand=True)  

        self.api_base_url = "http://127.0.0.1:8000"
        self.setup_ui()

    def setup_ui(self):
        """Sets up the login UI with a full gray background."""
        # ✅ Create a centered frame on top of the gray background
        self.frame = tk.Frame(self.canvas, bg="white", padx=30, pady=40, relief="raised", bd=3)
        self.frame.place(relx=0.5, rely=0.5, anchor="center")  # ✅ Keep centered

        title_label = tk.Label(self.frame, text="Login", font=("Arial", 20, "bold"), bg="white")
        title_label.pack(pady=15)

        username_label = tk.Label(self.frame, text="Username:", font=("Arial", 14), bg="white")
        username_label.pack(anchor="w")
        self.username_entry = ttk.Entry(self.frame, width=40)
        self.username_entry.pack(pady=6)

        password_label = tk.Label(self.frame, text="Password:", font=("Arial", 14), bg="white")
        password_label.pack(anchor="w")
        self.password_entry = ttk.Entry(self.frame, width=40, show="*")
        self.password_entry.pack(pady=8)

        login_button = ttk.Button(self.frame, text="Login", command=self.login)
        login_button.pack(pady=15, ipadx=20, ipady=5)

        register_button = tk.Button(
            self.root, text="Register", command=self.show_register_window,
            fg="blue", borderwidth=0, bg="#D3D3D3", font=("Arial", 12, "underline")
        )
        register_button.place(relx=0.5, rely=0.7, anchor="center")  # ✅ Keep centered

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
        self.register_window.geometry("700x500")
        self.register_window.state("zoomed")  # ✅ Zoomed full-screen
        
        # ✅ Create full gray background
        canvas = tk.Canvas(self.register_window, bg="#D3D3D3")
        canvas.pack(fill="both", expand=True)

        # ✅ Create a centered frame
        frame = tk.Frame(canvas, bg="white", padx=30, pady=30, relief="raised", bd=3)
        frame.place(relx=0.5, rely=0.5, anchor="center")  # ✅ Keep centered

        title_label = tk.Label(frame, text="Register", font=("Arial", 20, "bold"), bg="white")
        title_label.pack(pady=15)

        username_label = tk.Label(frame, text="Username:", font=("Arial", 14), bg="white")
        username_label.pack(anchor="w")
        reg_username_entry = ttk.Entry(frame, width=40)
        reg_username_entry.pack(pady=8)

        password_label = tk.Label(frame, text="Password:", font=("Arial", 14), bg="white")
        password_label.pack(anchor="w")
        reg_password_entry = ttk.Entry(frame, width=40, show="*")
        reg_password_entry.pack(pady=8)

        role_label = tk.Label(frame, text="Role:", font=("Arial", 14), bg="white")
        role_label.pack(anchor="w")
        role_combobox = ttk.Combobox(frame, values=["user", "admin"], state="readonly", font=("Arial", 12))
        role_combobox.pack(pady=8)
        role_combobox.current(0)

        register_button = ttk.Button(frame, text="Register", command=lambda: self.register(reg_username_entry, reg_password_entry, role_combobox))
        register_button.pack(pady=15, ipadx=20, ipady=5, anchor="center")

    def register(self, username_entry, password_entry, role_combobox):
        """Handles user registration."""
        username = username_entry.get()
        password = password_entry.get()
        role = role_combobox.get()

        if not username or not password:
            messagebox.showerror("Error", "Please enter both username and password.")
            return

        try:
            data = {"username": username, "password": password, "role": role}
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
