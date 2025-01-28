#dashboard
import tkinter as tk
from tkinter import ttk
from users_gui import UserManagement  # Import UserManagement correctly



class Dashboard:
    def __init__(self, root, token):
        self.root = root
        self.token = token
        self.root.title("Dashboard - Hotel Management System")
        self.root.geometry("800x600")
        
        # Base API URL
        self.api_base_url = "http://127.0.0.1:8000"  # Adjust to match your FastAPI base URL

        # UI Components for Dashboard
        self.setup_dashboard_ui()

    def setup_dashboard_ui(self):
        # Title Label
        title_label = ttk.Label(self.root, text="Welcome to the Dashboard", font=("Helvetica", 18))
        title_label.pack(pady=20)

        # Button for Users Management
        users_button = ttk.Button(self.root, text="Manage Users", command=self.manage_users)
        users_button.pack(pady=10)

        # Button for Rooms Management
        rooms_button = ttk.Button(self.root, text="Manage Rooms", command=self.manage_rooms)
        rooms_button.pack(pady=10)

        # Button for Bookings Management
        bookings_button = ttk.Button(self.root, text="Manage Bookings", command=self.manage_bookings)
        bookings_button.pack(pady=10)

        # Button for Payments Management
        payments_button = ttk.Button(self.root, text="Manage Payments", command=self.manage_payments)
        payments_button.pack(pady=10)

        # Logout Button
        logout_button = ttk.Button(self.root, text="Logout", command=self.logout)
        logout_button.pack(pady=20)

    def manage_users(self):
        # Create a new instance of UserManagement in a Toplevel window
        UserManagement(self.root, self.token)

    def manage_rooms(self):
        print("Manage Rooms button clicked")  # Placeholder for Rooms management logic

    def manage_bookings(self):
        print("Manage Bookings button clicked")  # Placeholder for Bookings management logic

    def manage_payments(self):
        print("Manage Payments button clicked")  # Placeholder for Payments management logic

    def logout(self):
        self.root.destroy()
        root = tk.Tk()  # You might want to return to a login screen after logging out
        from login_gui import LoginGUI  # Import the Login GUI if you have one
        app = LoginGUI(root)
        root.mainloop()
