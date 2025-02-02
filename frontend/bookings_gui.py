import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry  # Import DateEntry for date selection
import requests
from utils import BASE_URL


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
            #("Complimentary Booking", self.complimentary_booking),
            ("List Bookings", self.list_bookings),
            ("List By Status", self.list_bookings_by_status),
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

    def update_subheading(self, text, command):
        self.subheading_label.config(text=text)
        command()

    def create_booking(self):
        self.clear_right_frame()
        frame = tk.Frame(self.right_frame, bg="#ffffff", padx=20, pady=20)
        frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(frame, text="Create Booking Form", font=("Arial", 14, "bold"), bg="#ffffff").grid(row=0, columnspan=2, pady=10)

        # Labels & Entry fields
        fields = [
            ("Room Number", tk.Entry),
            ("Guest Name", tk.Entry),
            ("Phone Number", tk.Entry),
            ("Booking Type", ttk.Combobox),
            ("Arrival Date", DateEntry),
            ("Departure Date", DateEntry),
        ]

        self.entries = {}
        for i, (label, field_type) in enumerate(fields):
            tk.Label(frame, text=label, font=("Arial", 11), bg="#ffffff").grid(row=i+1, column=0, sticky="w", pady=5)
            if field_type == ttk.Combobox:
                entry = field_type(frame, values=["Checked-in", "Reservation", "Complimentary"], state="readonly", font=("Arial", 11))
            elif field_type == DateEntry:
                entry = field_type(frame, font=("Arial", 11), width=12, background='darkblue', foreground='white', borderwidth=2)
            else:
                entry = field_type(frame, font=("Arial", 11), width=25)
            entry.grid(row=i+1, column=1, padx=10, pady=5)
            self.entries[label] = entry

        # Submit Button
        submit_btn = ttk.Button(frame, text="Submit Booking", command=self.submit_booking, style="Bold.TButton")
        submit_btn.grid(row=len(fields)+1, columnspan=2, pady=10)

    def submit_booking(self):
        """Collects form data and sends a request to create a booking."""
        try:
            booking_data = {
                "room_number": self.entries["Room Number"].get(),
                "guest_name": self.entries["Guest Name"].get(),
                "phone_number": self.entries["Phone Number"].get(),
                "arrival_date": self.entries["Arrival Date"].get_date().strftime("%Y-%m-%d"),
                "departure_date": self.entries["Departure Date"].get_date().strftime("%Y-%m-%d"),
                "booking_type": self.entries["Booking Type"].get(),
            }

            if not all(booking_data.values()):  # Ensure all fields are filled
                messagebox.showerror("Error", "Please fill in all fields")
                return

            api_url = "http://127.0.0.1:8000/bookings/create/"  # Adjust if needed
            headers = {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}

            response = requests.post(api_url, json=booking_data, headers=headers)

            if response.status_code == 200:
                messagebox.showinfo("Success", "Booking created successfully!")
            else:
                messagebox.showerror("Error", response.json().get("detail", "Booking failed."))

        except KeyError as e:
            messagebox.showerror("Error", f"Missing entry field: {e}")
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Error", f"Request failed: {e}")

    
    
    def list_bookings(self):
        self.clear_right_frame()
        
        # Create a new frame for the table with scrollable functionality
        frame = tk.Frame(self.right_frame, bg="#ffffff", padx=10, pady=10)
        frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(frame, text="List Bookings", font=("Arial", 14, "bold"), bg="#ffffff").pack(pady=10)

        filter_frame = tk.Frame(frame, bg="#ffffff")
        filter_frame.pack(pady=5)

        tk.Label(filter_frame, text="Start Date:", font=("Arial", 11), bg="#ffffff").grid(row=0, column=0, padx=5, pady=5)
        self.start_date = DateEntry(filter_frame, font=("Arial", 11))
        self.start_date.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(filter_frame, text="End Date:", font=("Arial", 11), bg="#ffffff").grid(row=0, column=2, padx=5, pady=5)
        self.end_date = DateEntry(filter_frame, font=("Arial", 11))
        self.end_date.grid(row=0, column=3, padx=5, pady=5)

        fetch_btn = ttk.Button(
            filter_frame,
            text="Fetch Bookings",
            command=lambda: self.fetch_bookings(self.start_date, self.end_date)
        )
        fetch_btn.grid(row=0, column=4, padx=10, pady=5)

        # Create a frame to hold the treeview and scrollbars
        table_frame = tk.Frame(frame, bg="#ffffff")
        table_frame.pack(fill=tk.BOTH, expand=True)

        # Define Treeview columns
        columns = ("ID", "Room", "Guest", "Arrival", "Departure", "Status", "Number of Days", 
                "Booking Type", "Phone Number", "Booking Date", "Payment Status", "Booking Cost")

        # Create a Treeview widget
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings")

        # Define headings and set column widths
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120, anchor="center")

        # Pack the Treeview inside a scrollable frame
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Add vertical scrollbar
        y_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        y_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscroll=y_scroll.set)

        # Add horizontal scrollbar
        x_scroll = ttk.Scrollbar(frame, orient="horizontal", command=self.tree.xview)
        x_scroll.pack(fill=tk.X)
        self.tree.configure(xscroll=x_scroll.set)


    def fetch_bookings(self, start_date_entry, end_date_entry):
        """Fetch bookings from the API and populate the table."""
        api_url = "http://127.0.0.1:8000/bookings/list"  # Ensure correct endpoint
        params = {
            "start_date": start_date_entry.get_date().strftime("%Y-%m-%d"),
            "end_date": end_date_entry.get_date().strftime("%Y-%m-%d"),
        }
        headers = {"Authorization": f"Bearer {self.token}"}

        try:
            response = requests.get(api_url, params=params, headers=headers)
            if response.status_code == 200:
                data = response.json()
                print("API Response:", data)  # Debugging output

                if isinstance(data, dict) and "bookings" in data:
                    bookings = data["bookings"]
                elif isinstance(data, list):
                    bookings = data
                else:
                    messagebox.showerror("Error", "Unexpected API response format")
                    return

                self.tree.delete(*self.tree.get_children())  # Clear table

                for booking in bookings:
                    self.tree.insert("", "end", values=(
                        booking.get("id", ""),
                        booking.get("room_number", ""),
                        booking.get("guest_name", ""),
                        booking.get("arrival_date", ""),
                        booking.get("departure_date", ""),
                        booking.get("status", ""),
                        booking.get("number_of_days", ""),
                        booking.get("booking_type", ""),
                        booking.get("phone_number", ""),
                        booking.get("booking_date", ""),
                        booking.get("payment_status", ""),
                        booking.get("booking_cost", ""),
                    ))
            else:
                messagebox.showerror("Error", response.json().get("detail", "Failed to retrieve bookings."))
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Error", f"Request failed: {e}")

    def clear_right_frame(self):
        for widget in self.right_frame.winfo_children():
            widget.pack_forget()


    
    def list_bookings_by_status(self):
        self.clear_right_frame()
        
        # Create a new frame for the table with scrollable functionality
        frame = tk.Frame(self.right_frame, bg="#ffffff", padx=10, pady=10)
        frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(frame, text="List Bookings by Status", font=("Arial", 14, "bold"), bg="#ffffff").pack(pady=10)
        
        filter_frame = tk.Frame(frame, bg="#ffffff")
        filter_frame.pack(pady=5)
        
        tk.Label(filter_frame, text="Status:", font=("Arial", 11), bg="#ffffff").grid(row=0, column=0, padx=5, pady=5)
        status_options = ["checked-in", "reserved", "checked-out", "cancelled", "complimentary"]
        self.status_var = tk.StringVar()
        self.status_var.set(status_options[0])  # Default to first status
        status_menu = ttk.Combobox(filter_frame, textvariable=self.status_var, values=status_options, state="readonly")
        status_menu.grid(row=0, column=1, padx=5, pady=5)
        
        tk.Label(filter_frame, text="Start Date:", font=("Arial", 11), bg="#ffffff").grid(row=0, column=2, padx=5, pady=5)
        self.start_date = DateEntry(filter_frame, font=("Arial", 11))
        self.start_date.grid(row=0, column=3, padx=5, pady=5)
        
        tk.Label(filter_frame, text="End Date:", font=("Arial", 11), bg="#ffffff").grid(row=0, column=4, padx=5, pady=5)
        self.end_date = DateEntry(filter_frame, font=("Arial", 11))
        self.end_date.grid(row=0, column=5, padx=5, pady=5)
        
        fetch_btn = ttk.Button(
            filter_frame,
            text="Fetch Bookings",
            command=self.fetch_bookings_by_status
        )
        fetch_btn.grid(row=0, column=6, padx=10, pady=5)
        
        # Table Frame
        table_frame = tk.Frame(frame, bg="#ffffff")
        table_frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ("ID", "Room", "Guest", "Arrival", "Departure", "Status", "Number of Days", 
                "Booking Type", "Phone Number", "Booking Date", "Payment Status", "Booking Cost")
        
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120, anchor="center")
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Scrollbars
        y_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        y_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscroll=y_scroll.set)
        
        x_scroll = ttk.Scrollbar(frame, orient="horizontal", command=self.tree.xview)
        x_scroll.pack(fill=tk.X)
        self.tree.configure(xscroll=x_scroll.set)

    def fetch_bookings_by_status(self):
        """Fetch bookings based on status and date filters."""
        api_url = "http://127.0.0.1:8000/bookings/status"
        
        params = {
            "status": self.status_var.get(),
            "start_date": self.start_date.get_date().strftime("%Y-%m-%d"),
            "end_date": self.end_date.get_date().strftime("%Y-%m-%d"),
        }

        headers = {"Authorization": f"Bearer {self.token}"}

        try:
            response = requests.get(api_url, params=params, headers=headers)
            if response.status_code == 200:
                data = response.json()
                print("API Response:", data)  # Debugging output
                

                if "bookings" in data:
                    bookings = data["bookings"]
                    self.tree.delete(*self.tree.get_children())  # Clear table

                    for booking in bookings:
                        self.tree.insert("", "end", values=(
                            booking.get("id", ""),
                            booking.get("room_number", ""),
                            booking.get("guest_name", ""),
                            booking.get("arrival_date", ""),
                            booking.get("departure_date", ""),
                            booking.get("status", ""),
                            booking.get("number_of_days", ""),
                            booking.get("booking_type", ""),
                            booking.get("phone_number", ""),
                            booking.get("booking_date", ""),
                            booking.get("payment_status", ""),
                            booking.get("booking_cost", ""),
                        ))
                else:
                    messagebox.showinfo("No Results", "No bookings found for the selected filters.")

            else:
                messagebox.showerror("Error", response.json().get("detail", "Failed to retrieve bookings."))

        except requests.exceptions.RequestException as e:
            messagebox.showerror("Error", f"Request failed: {e}")

    def clear_right_frame(self):
        for widget in self.right_frame.winfo_children():
            widget.pack_forget()    
            

    #def complimentary_booking(self):
        #messagebox.showinfo("Info", "Complimentary Booking Selected")
    
    #def list_bookings(self):
        #messagebox.showinfo("Info", "List Bookings Selected")
    
    #def list_by_status(self):
       #messagebox.showinfo("Info", "List By Status Selected")
    
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