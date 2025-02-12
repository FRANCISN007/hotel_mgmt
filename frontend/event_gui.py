import tkinter as tk
from tkinter import ttk, messagebox
import requests
from utils import BASE_URL

class EventManagement:
    def __init__(self, root, token):
        self.root = tk.Toplevel(root)
        self.root.title("Event Management")
        self.root.geometry("1000x600")
        
        # Centering the window
        self.root.update_idletasks()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        window_width = 1000
        window_height = 600
        position_x = (screen_width // 2) - (window_width // 2)
        position_y = (screen_height // 2) - (window_height // 2)
        self.root.geometry(f"{window_width}x{window_height}+{position_x}+{position_y}")
        
        self.token = token
        self.root.configure(bg="#f0f0f0")

        style = ttk.Style()
        style.configure("Treeview.Heading", font=("Helvetica", 12, "bold"))
        style.configure("Treeview", font=("Helvetica", 11))

        # Header Section
        self.header_frame = tk.Frame(self.root, bg="#d9d9d9", height=50)
        self.header_frame.pack(fill=tk.X)
        self.header_label = tk.Label(self.header_frame, text="Event Management", 
                                     fg="black", bg="#d9d9d9", font=("Helvetica", 16, "bold"))
        self.header_label.pack(pady=10)

        # Sidebar Section
        self.left_frame = tk.Frame(self.root, bg="#d9d9d9", width=200)
        self.left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

        # Right Section
        self.right_frame = tk.Frame(self.root, bg="#f0f0f0", width=700)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Subheading for dynamic section title
        self.subheading_label = tk.Label(self.right_frame, text="Select an option", 
                                         font=("Helvetica", 12, "bold"), fg="#333333", bg="#f0f0f0")
        self.subheading_label.pack(pady=10)

        # Event action buttons
        self.buttons = []
        event_buttons = [
            ("➕Create Event", self.create_event),
            ("📑List Events", self.list_events),
            ("📑List By Status", self.list_bookings_by_status),
            ("🔎Search by Event ID", self.search_event_by_id),
            ("✏️Update Event", self.update_event),
            ("❌Cancel Event", self.cancel_event),
        ]

        for text, command in event_buttons:
            btn = tk.Button(self.left_frame, text=text, 
                            command=lambda t=text, c=command: self.update_subheading(t, c),
                            width=19, font=("Helvetica", 10, "bold"), anchor="w", padx=10, 
                            bg="#e0e0e0", fg="black")
            btn.bind("<Enter>", lambda e, b=btn: b.config(bg="#007BFF", fg="white"))  
            btn.bind("<Leave>", lambda e, b=btn: b.config(bg="#e0e0e0", fg="black"))
            btn.pack(pady=5, padx=10, anchor="w", fill="x")
            self.buttons.append(btn)
        
        # Separation line
        tk.Label(self.left_frame, text="", bg="#d9d9d9").pack(pady=5)
        
        # Event Payment action buttons
        payment_buttons = [
            ("➕Create Event Payment", self.create_event_payment),
            ("📑List Event Payments", self.list_events_payment),
            ("📑List Payment By Status", self.list_Payment_by_status),
            ("🔎Search by Payment ID", self.search_Payment_by_id),
            ("❌Void Payment", self.void_payment),
        ]

        for text, command in payment_buttons:
            btn = tk.Button(self.left_frame, text=text, 
                            command=lambda t=text, c=command: self.update_subheading(t, c),
                            width=19, font=("Helvetica", 10, "bold"), anchor="w", padx=10, 
                            bg="#e0e0e0", fg="black")
            btn.bind("<Enter>", lambda e, b=btn: b.config(bg="#DC143C", fg="white"))  
            btn.bind("<Leave>", lambda e, b=btn: b.config(bg="#e0e0e0", fg="black"))
            btn.pack(pady=5, padx=10, anchor="w", fill="x")
            self.buttons.append(btn)

    def update_subheading(self, text, command):
        self.subheading_label.config(text=text)
        command()
    
    def create_event(self):
        pass
    
    def list_events(self):
        pass
    
    def list_bookings_by_status(self):
        pass
    
    def search_event_by_id(self):
        pass
    
    def update_event(self):
        pass
    
    def cancel_event(self):
        pass
    
    def create_event_payment(self):
        pass
    
    def list_events_payment(self):
        pass
    
    def list_Payment_by_status(self):
        pass
    
    def search_Payment_by_id(self):
        pass
    
    def void_payment(self):
        pass
