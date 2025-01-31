import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
import requests

# Backend API URL
API_URL = "http://127.0.0.1:8000/bookings"

class BookingManagement:
    def __init__(self, root, token):  
        self.token = token
        
        # Create a new window (Toplevel)
        self.window = tk.Toplevel(root)
        self.window.title("Booking Management")
        self.window.geometry("800x600")  # Standard window size
        self.window.resizable(False, False)  # Prevent resizing for consistency
        
        # Create a frame for layout
        self.frame = ttk.Frame(self.window, padding=10)
        self.frame.pack(fill="both", expand=True)

        # Labels & Entry Fields
        ttk.Label(self.frame, text="Room Number:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.room_number_entry = ttk.Entry(self.frame)
        self.room_number_entry.grid(row=0, column=1, padx=10, pady=5, sticky="w")

        ttk.Label(self.frame, text="Guest Name:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.guest_name_entry = ttk.Entry(self.frame)
        self.guest_name_entry.grid(row=1, column=1, padx=10, pady=5, sticky="w")

        ttk.Label(self.frame, text="Arrival Date:").grid(row=2, column=0, padx=10, pady=5, sticky="w")
        self.arrival_date_entry = DateEntry(self.frame, width=12, background='darkblue', foreground='white', borderwidth=2)
        self.arrival_date_entry.grid(row=2, column=1, padx=10, pady=5, sticky="w")

        ttk.Label(self.frame, text="Departure Date:").grid(row=3, column=0, padx=10, pady=5, sticky="w")
        self.departure_date_entry = DateEntry(self.frame, width=12, background='darkblue', foreground='white', borderwidth=2)
        self.departure_date_entry.grid(row=3, column=1, padx=10, pady=5, sticky="w")

        ttk.Label(self.frame, text="Phone Number:").grid(row=4, column=0, padx=10, pady=5, sticky="w")
        self.phone_number_entry = ttk.Entry(self.frame)
        self.phone_number_entry.grid(row=4, column=1, padx=10, pady=5, sticky="w")

        # Booking Type Dropdown
        ttk.Label(self.frame, text="Booking Type:").grid(row=5, column=0, padx=10, pady=5, sticky="w")
        self.booking_type_var = tk.StringVar()
        self.booking_type_dropdown = ttk.Combobox(self.frame, textvariable=self.booking_type_var, values=["C", "R"], state="readonly")
        self.booking_type_dropdown.grid(row=5, column=1, padx=10, pady=5, sticky="w")

        # Buttons
        self.create_btn = ttk.Button(self.frame, text="Create Booking", command=self.create_booking)
        self.create_btn.grid(row=6, column=0, columnspan=2, pady=10)

        self.view_btn = ttk.Button(self.frame, text="View All Bookings", command=self.view_bookings)
        self.view_btn.grid(row=7, column=0, columnspan=2, pady=5)

        # Treeview for displaying bookings
        self.tree_frame = ttk.Frame(self.window)
        self.tree_frame.pack(pady=10, padx=10, fill="both", expand=True)

        self.tree = ttk.Treeview(self.tree_frame, columns=("id", "room_number", "guest_name", "status"), show="headings", height=10)
        self.tree.heading("id", text="ID")
        self.tree.heading("room_number", text="Room Number")
        self.tree.heading("guest_name", text="Guest Name")
        self.tree.heading("status", text="Status")

        self.tree.column("id", width=50, anchor="center")
        self.tree.column("room_number", width=100, anchor="center")
        self.tree.column("guest_name", width=200, anchor="w")
        self.tree.column("status", width=100, anchor="center")

        self.tree.pack(fill="both", expand=True)

    def create_booking(self):
        data = {
            "room_number": self.room_number_entry.get(),
            "guest_name": self.guest_name_entry.get(),
            "arrival_date": self.arrival_date_entry.get_date().isoformat(),
            "departure_date": self.departure_date_entry.get_date().isoformat(),
            "phone_number": self.phone_number_entry.get(),
            "booking_type": self.booking_type_var.get(),
        }
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.post(f"{API_URL}/create/", json=data, headers=headers)
        if response.status_code == 200:
            messagebox.showinfo("Success", "Booking created successfully!")
        else:
            messagebox.showerror("Error", response.json().get("detail", "Failed to create booking"))

    def view_bookings(self):
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(API_URL, headers=headers)
        if response.status_code == 200:
            for row in self.tree.get_children():
                self.tree.delete(row)
            bookings = response.json()
            for booking in bookings:
                self.tree.insert("", "end", values=(booking["id"], booking["room_number"], booking["guest_name"], booking["status"]))
        else:
            messagebox.showerror("Error", "Failed to fetch bookings")

