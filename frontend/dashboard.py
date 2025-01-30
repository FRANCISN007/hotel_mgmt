import tkinter as tk
from tkinter import ttk
from users_gui import UserManagement
from rooms_gui import RoomManagement
from utils import load_token, get_user_role 
from tkinter import messagebox  # Add this line



class Dashboard:
    def __init__(self, root, token):
        self.root = root
        self.token = token
        self.root.title("Dashboard - Hotel Management System")
        self.root.geometry("800x600")
        
        # Fetch and store user role
        self.user_role = get_user_role(self.token)  # Fetch the role from API


        # UI Components for Dashboard
        self.setup_dashboard_ui()

    def setup_dashboard_ui(self):
        # Title Label
        title_label = ttk.Label(self.root, text="Welcome to the Dashboard", font=("Helvetica", 18))
        title_label.pack(pady=20)

        # Buttons for Management Modules
        buttons = [
            ("Manage Users", self.manage_users),
            ("Manage Rooms", self.manage_rooms),
            ("Manage Bookings", self.manage_bookings),
            ("Manage Payments", self.manage_payments),
        ]

        for text, command in buttons:
            button = ttk.Button(self.root, text=text, command=command)
            button.pack(pady=10)

        # Logout Button
        logout_button = ttk.Button(self.root, text="Logout", command=self.logout)
        logout_button.pack(pady=20)

    def manage_users(self):
        if self.user_role != "admin":
            messagebox.showerror("Access Denied", "Insufficient permissions")
            return
        UserManagement(self.root, self.token)

    def manage_rooms(self):
        RoomManagement(self.root, self.token)  # Open RoomManagement
        
    def manage_bookings(self):
        print("Manage Bookings functionality coming soon!")

    def manage_payments(self):
        print("Manage Payments functionality coming soon!")

    def logout(self):
        self.root.destroy()
        root = tk.Tk()
        from login_gui import LoginGUI
        LoginGUI(root)
        root.mainloop()


if __name__ == "__main__":
    token = load_token()
    if token:
        root = tk.Tk()
        Dashboard(root, token)
        root.mainloop()
    else:
        print("No token found. Please log in.")
