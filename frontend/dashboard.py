import tkinter as tk
from tkinter import ttk
from users_gui import UserManagement
from rooms_gui import RoomManagement
from bookings_gui import BookingManagement
from payment_gui import PaymentManagement
from event_gui import EventManagement  # Import Event Management
from utils import load_token, get_user_role
from tkinter import messagebox  # For access control popups

class Dashboard:
    def __init__(self, root, token):
        self.root = root
        self.token = token
        self.root.title("Dashboard - Hotel & Event Management System")
        
        # Make the window full screen
        self.root.state("zoomed")

        # Fetch screen width and height
        self.screen_width = self.root.winfo_screenwidth()
        self.screen_height = self.root.winfo_screenheight()

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

        title_label = tk.Label(header_frame, text="Hotel & Event Management Dashboard", fg="white",
                            bg="#004080", font=("Helvetica", 18, "bold"))
        title_label.pack(pady=10)

        # User Role Display
        role_label = tk.Label(self.root, text=f"Logged in as: {self.user_role.capitalize()}",
                            font=("Arial", 12, "italic"), fg="#333", bg="#f0f0f0")
        role_label.pack(pady=10)

        # Main Buttons Frame (Centered)
        button_frame = tk.Frame(self.root, bg="#f0f0f0")
        button_frame.pack(pady=20)

        # Button Configurations
        button_font = ("Helvetica", 14, "bold")
        button_bg = "#0078D7"
        hover_bg = "#005BBB"
        text_color = "white"
        shadow_color = "#003E80"

        def on_enter(event):
            event.widget.config(bg=hover_bg, relief="sunken")

        def on_leave(event):
            event.widget.config(bg=button_bg, relief="raised")

        buttons = [
            ("Manage Users", self.manage_users),
            ("Manage Rooms", self.manage_rooms),
            ("Manage Bookings", self.manage_bookings),
            ("Manage Payments", self.manage_payments),
        ]

        for text, command in buttons:
            btn = tk.Button(button_frame, text=text, command=command,
                            font=button_font, width=20, height=1,
                            bg=button_bg, fg=text_color, bd=3, relief="raised",
                            highlightbackground=shadow_color, highlightthickness=2)
            btn.pack(pady=10)

            btn.bind("<Enter>", on_enter)
            btn.bind("<Leave>", on_leave)

        # Manage Events Button (Bigger & Different Color)
        event_button = tk.Button(button_frame, text="📅 Manage Events", command=self.manage_events,
                                 font=("Helvetica", 16, "bold"), width=25, height=2,
                                 bg="#FF5733", fg="white", bd=4, relief="raised",
                                 highlightbackground="#8B0000", highlightthickness=3)
        event_button.pack(pady=20)

        def event_on_enter(event):
            event.widget.config(bg="#D84315", relief="sunken")

        def event_on_leave(event):
            event.widget.config(bg="#FF5733", relief="raised")

        event_button.bind("<Enter>", event_on_enter)
        event_button.bind("<Leave>", event_on_leave)

        # Circular Logout Button (Smaller)
        logout_frame = tk.Frame(self.root, bg="#f0f0f0")
        logout_frame.pack(pady=20)

        logout_button = tk.Button(logout_frame, text="Logout", command=self.logout,
                                font=("Helvetica", 12, "bold"), width=10, height=0,
                                bg="#8B0000", fg="white", bd=3, relief="ridge",
                                highlightbackground="black", highlightthickness=2,
                                cursor="hand2")

        logout_button.pack(ipadx=10, ipady=8)

        def logout_hover_enter(event):
            logout_button.config(bg="darkred", relief="sunken")

        def logout_hover_leave(event):
            logout_button.config(bg="#8B0000", relief="ridge")

        logout_button.bind("<Enter>", logout_hover_enter)
        logout_button.bind("<Leave>", logout_hover_leave)

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
        PaymentManagement(self.root, self.token)
    
    def manage_events(self):
        EventManagement(self.root, self.token)  # Ensure username is passed



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
