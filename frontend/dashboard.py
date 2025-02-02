import tkinter as tk
from tkinter import ttk
from users_gui import UserManagement
from rooms_gui import RoomManagement
from bookings_gui import BookingManagement
from utils import load_token, get_user_role
from tkinter import messagebox  # For access control popups

class Dashboard:
    def __init__(self, root, token):
        self.root = root
        self.token = token
        self.root.title("Dashboard - Hotel Management System")
        self.root.geometry("800x600")
        self.root.configure(bg="#f0f0f0")  # Light gray background

        # Fetch and store user role
        self.user_role = get_user_role(self.token)
        

        # UI Components
        self.setup_dashboard_ui()
        
        style = ttk.Style()
        style.configure("TButton", font=("Helvetica", 12))  # Increase font size for buttons

    def setup_dashboard_ui(self):
        # Header Frame
        header_frame = tk.Frame(self.root, bg="#004080", height=60)
        header_frame.pack(fill=tk.X)

        title_label = tk.Label(header_frame, text="Hotel Management Dashboard", fg="white", 
                               bg="#004080", font=("Helvetica", 18, "bold"))
        title_label.pack(pady=10)
        
        # User Role Display
        role_label = tk.Label(self.root, text=f"Logged in as: {self.user_role.capitalize()}",
                              font=("Arial", 12, "italic"), fg="#333", bg="#f0f0f0")
        role_label.pack(pady=10)

        # Main Buttons Frame
        button_frame = tk.Frame(self.root, bg="#f0f0f0")
        button_frame.pack(pady=20)

        

        buttons = [
            ("Manage Users", self.manage_users),
            ("Manage Rooms", self.manage_rooms),
            ("Manage Bookings", self.manage_bookings),
            ("Manage Payments", self.manage_payments),
        ]
        

        for text, command in buttons:
            btn = ttk.Button(button_frame, text=text, command=command, width=25)
            btn.pack(pady=10)

        # Logout Button at Bottom
        logout_button = ttk.Button(self.root, text="Logout", command=self.logout, width=20)
        logout_button.pack(pady=30)
        
        

    def manage_users(self):
        if self.user_role != "admin":
            messagebox.showerror("Access Denied", "You do not have permission to manage users.")
            return
        UserManagement(self.root, self.token)

    def manage_rooms(self):
        RoomManagement(self.root, self.token)
    
    def manage_bookings(self):
        BookingManagement(self.root, self.token)
        

    def manage_payments(self):
        messagebox.showinfo("Coming Soon", "Manage Payments functionality will be added soon!")

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
