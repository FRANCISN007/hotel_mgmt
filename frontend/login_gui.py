import tkinter as tk
from tkinter import ttk, messagebox
import requests
from dashboard import Dashboard  # Import the Dashboard clas

class LoginGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Hotel Management System")
        self.root.geometry("700x500")
        self.root.state("zoomed")  # ✅ Ensures full-screen mode
        self.api_base_url = "http://127.0.0.1:8000"
        
        

        # ✅ Gray background (Zoomed to full screen)
        self.canvas = tk.Canvas(self.root, bg="#D3D3D3")
        self.canvas.pack(fill="both", expand=True)

        # ✅ Main frame where login/register forms will appear
        self.main_frame = tk.Frame(self.canvas, bg="#D3D3D3")
        self.main_frame.place(relx=0.5, rely=0.5, anchor="center")  # ✅ Always centered

        # Show login UI initially*****
        self.show_login_ui()
        
        

    def show_login_ui(self):
        """Displays the login UI (hides registration UI if open)."""
        self.clear_window()

        # ✅ Centered white frame (Login Form)
        self.frame = tk.Frame(self.main_frame, bg="white", padx=30, pady=30, relief="raised", bd=3)
        self.frame.pack()

        # ✅ Modified Login Title with Light Gray Border
        title_label = tk.Label(
            self.frame,
            text="Login",
            font=("Arial", 15, "bold"),
            bg="#D3D3D3",  # Light gray background for the title
            fg="black",
            borderwidth=2,  # Light border thickness
            relief="solid",  # Gives a bordered effect
            padx=10,  # Adds horizontal padding
            pady=5  # Adds vertical padding (increases height)
        )
        title_label.pack(pady=15)

        # Username Field with a Frame
        username_label = tk.Label(self.frame, text="Username:", font=("Arial", 12), bg="white")
        username_label.pack(anchor="w")

        username_frame = tk.Frame(self.frame, bg="#D3D3D3", relief="sunken", borderwidth=2)
        username_frame.pack(pady=6, fill="x", padx=5)
        self.username_entry = tk.Entry(username_frame, width=38, borderwidth=0, bg="white")
        self.username_entry.pack(padx=2, pady=2)

        # Password Field with a Frame
        password_label = tk.Label(self.frame, text="Password:", font=("Arial", 12), bg="white")
        password_label.pack(anchor="w")

        password_frame = tk.Frame(self.frame, bg="#D3D3D3", relief="sunken", borderwidth=2)
        password_frame.pack(pady=8, fill="x", padx=5)
        self.password_entry = tk.Entry(password_frame, width=38, show="*", borderwidth=0, bg="white")
        self.password_entry.pack(padx=2, pady=2)


        login_button = ttk.Button(self.frame, text="Login", command=self.login)
        login_button.pack(pady=15, ipadx=20, ipady=5)

        register_button = tk.Button(
            self.frame, text="Register", command=self.show_register_ui,
            fg="blue", borderwidth=0, bg="white", font=("Arial", 12, "underline")
        )
        register_button.pack(pady=5)

        
        
    def show_register_ui(self):
        """Displays the registration UI (hides login UI)."""
        self.clear_window()

        # ✅ Centered white frame (Register Form)
        self.frame = tk.Frame(self.main_frame, bg="white", padx=30, pady=30, relief="raised", bd=3)
        self.frame.pack()

        title_label = tk.Label(self.frame, text="Register", font=("Arial", 15, "bold"), bg="white")
        title_label.pack(pady=15)

        # ✅ Username Field with a Frame (Sinking Effect)
        username_label = tk.Label(self.frame, text="Username:", font=("Arial", 12), bg="white")
        username_label.pack(anchor="w")

        username_frame = tk.Frame(self.frame, bg="#D3D3D3", relief="sunken", borderwidth=2)
        username_frame.pack(pady=6, fill="x", padx=5)
        self.reg_username_entry = tk.Entry(username_frame, width=38, borderwidth=0, bg="white")
        self.reg_username_entry.pack(padx=2, pady=2)

        # ✅ Password Field with a Frame
        password_label = tk.Label(self.frame, text="Password:", font=("Arial", 12), bg="white")
        password_label.pack(anchor="w")

        password_frame = tk.Frame(self.frame, bg="#D3D3D3", relief="sunken", borderwidth=2)
        password_frame.pack(pady=8, fill="x", padx=5)
        self.reg_password_entry = tk.Entry(password_frame, width=38, show="*", borderwidth=0, bg="white")
        self.reg_password_entry.pack(padx=2, pady=2)

        # ✅ Role Dropdown (No Sinking Needed)
        role_label = tk.Label(self.frame, text="Role:", font=("Arial", 12), bg="white")
        role_label.pack(anchor="w")
        self.role_combobox = ttk.Combobox(self.frame, values=["user", "admin"], state="readonly", font=("Arial", 12))
        self.role_combobox.pack(pady=8)
        self.role_combobox.current(0)
        self.role_combobox.bind("<<ComboboxSelected>>", self.toggle_admin_password)

        # ✅ Admin Password Field (Initially Hidden)
        self.admin_password_frame = tk.Frame(self.frame, bg="white")

        self.reg_admin_password_label = tk.Label(self.admin_password_frame, text="Admin Password:", font=("Arial", 12), bg="white")

        admin_password_frame = tk.Frame(self.admin_password_frame, bg="#D3D3D3", relief="sunken", borderwidth=2)
        self.reg_admin_password_entry = tk.Entry(admin_password_frame, width=38, show="*", borderwidth=0, bg="white")

        # Packing Admin Password Fields (Initially Hidden)
        self.admin_password_frame.pack_forget()
        self.reg_admin_password_label.pack_forget()
        admin_password_frame.pack_forget()
        self.reg_admin_password_entry.pack_forget()

        register_button = ttk.Button(self.frame, text="Register", command=self.register)
        register_button.pack(pady=15, ipadx=20, ipady=5)

        back_button = tk.Button(
            self.frame, text="Back to Login", command=self.show_login_ui,
            fg="blue", borderwidth=0, bg="white", font=("Arial", 12, "underline")
        )
        back_button.pack(pady=5)

    def toggle_admin_password(self, event):
        """Shows/hides the admin password field based on role selection."""
        if self.role_combobox.get() == "admin":
            self.admin_password_frame.pack(pady=8, anchor="w", fill="x")
            self.reg_admin_password_label.pack(anchor="w")

            # Pack the sinking frame and entry
            self.reg_admin_password_entry.master.pack(pady=6, fill="x", padx=5)
            self.reg_admin_password_entry.pack(padx=2, pady=2)
        else:
            self.admin_password_frame.pack_forget()
            self.reg_admin_password_label.pack_forget()
            self.reg_admin_password_entry.master.pack_forget()
            self.reg_admin_password_entry.pack_forget()


    
    
    def clear_window(self):
        """Removes all widgets from the window to switch between forms."""
        for widget in self.main_frame.winfo_children():
            widget.destroy()

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
            self.show_login_ui()  # ✅ Switch back to login after successful registration
        except requests.RequestException as e:
            messagebox.showerror("Error", f"Registration failed: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = LoginGUI(root)
    root.mainloop()
