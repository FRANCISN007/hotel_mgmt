import tkinter as tk
from tkinter import ttk, messagebox

class BookingManagement:
    def __init__(self, root, token):
        self.root = tk.Toplevel(root)
        self.root.title("Booking Management")
        self.root.geometry("900x600")
        self.token = token
        self.root.configure(bg="#f0f0f0")

        # Header Section
        self.header_frame = tk.Frame(self.root, bg="#A0A0A0", height=50)
        self.header_frame.pack(fill=tk.X)

        self.header_label = tk.Label(self.header_frame, text="Booking Management", 
                                     fg="white", bg="#A0A0A0", font=("Helvetica", 16, "bold"))
        self.header_label.pack(pady=10)

        # Sidebar Section
        self.left_frame = tk.Frame(self.root, bg="#A0A0A0", width=200)
        self.left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

        self.right_frame = tk.Frame(self.root, bg="#ffffff", width=700)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Subheading for dynamic section title
        self.subheading_label = tk.Label(self.right_frame, text="Select an option", 
                                         font=("Helvetica", 12, "bold"), fg="#606060", bg="#ffffff")
        self.subheading_label.pack(pady=10)

        # Booking action buttons
        buttons = [
            ("Create Booking", self.create_booking),
            ("Complimentary Booking", self.complimentary_booking),
            ("List Bookings", self.list_bookings),
            ("List By Status", self.list_by_status),
            ("Search Booking", self.search_booking),
            ("List By ID", self.list_by_id),
            ("List By Room", self.list_by_room),
            ("Update Booking", self.update_booking),
            ("Guest Checkout", self.guest_checkout),
            ("Cancel Booking", self.cancel_booking),
        ]

        for text, command in buttons:
            btn = ttk.Button(self.left_frame, text=text, command=lambda t=text, c=command: self.update_subheading(t, c),
                             width=25, style="Bold.TButton")
            btn.pack(pady=5, padx=10, anchor="w")

        # Configure button styles
        style = ttk.Style()
        style.configure("Bold.TButton", font=("Helvetica", 10, "bold"))

        # Create Booking Section
        self.create_booking_frame = tk.Frame(self.right_frame, bg="#ffffff", padx=10, pady=10)
        self.create_booking_content = tk.Frame(self.create_booking_frame, bg="#ffffff")

        self.create_booking_label = tk.Label(self.create_booking_content, text="Create Booking Form", 
                                             font=("Arial", 12), bg="#ffffff")
        self.create_booking_label.pack(pady=20)

    def update_subheading(self, text, command):
        self.subheading_label.config(text=text)
        command()

    def create_booking(self):
        self.clear_right_frame()
        self.create_booking_frame.pack(fill=tk.BOTH, expand=True)
        self.create_booking_content.pack(fill=tk.BOTH, expand=True)

    def complimentary_booking(self):
        messagebox.showinfo("Info", "Complimentary Booking Selected")
    
    def list_bookings(self):
        messagebox.showinfo("Info", "List Bookings Selected")
    
    def list_by_status(self):
        messagebox.showinfo("Info", "List By Status Selected")
    
    def search_booking(self):
        messagebox.showinfo("Info", "Search Booking Selected")
    
    def list_by_id(self):
        messagebox.showinfo("Info", "List By ID Selected")
    
    def list_by_room(self):
        messagebox.showinfo("Info", "List By Room Selected")
    
    def update_booking(self):
        messagebox.showinfo("Info", "Update Booking Selected")
    
    def guest_checkout(self):
        messagebox.showinfo("Info", "Guest Checkout Selected")
    
    def cancel_booking(self):
        messagebox.showinfo("Info", "Cancel Booking Selected")
    
    def clear_right_frame(self):
        for widget in self.right_frame.winfo_children():
            widget.pack_forget()

if __name__ == "__main__":
    root = tk.Tk()
    BookingManagement(root, token="dummy_token")
    root.mainloop()
