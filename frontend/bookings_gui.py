import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
import requests
from utils import BASE_URL

class BookingManagement:
    def __init__(self, root, token):
        self.root = tk.Toplevel(root)
        self.root.title("Booking Management")
        self.root.geometry("900x600")
        self.token = token
        self.root.configure(bg="#f0f0f0")  # Very Light Gray (Same as Payment Management)

        style = ttk.Style()
        style.configure("Treeview.Heading", font=("Helvetica", 12, "bold"))
        style.configure("Treeview", font=("Helvetica", 11))  # Increase row font size

        # Header Section 
        self.header_frame = tk.Frame(self.root, bg="#d9d9d9", height=50)
        self.header_frame.pack(fill=tk.X)

        self.header_label = tk.Label(self.header_frame, text="Booking Management", 
                                     fg="black", bg="#d9d9d9", font=("Helvetica", 16, "bold"))
        self.header_label.pack(pady=10)

        # Sidebar Section 
        self.left_frame = tk.Frame(self.root, bg="#d9d9d9", width=200)
        self.left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

        # Right Section (Light Gray Background)
        self.right_frame = tk.Frame(self.root, bg="#f0f0f0", width=700)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Subheading for dynamic section title 
        self.subheading_label = tk.Label(self.right_frame, text="Select an option", 
                                         font=("Helvetica", 12, "bold"), fg="#333333", bg="#f0f0f0")
        self.subheading_label.pack(pady=10)

        # Booking action buttons 
        self.buttons = []
        buttons = [
            ("Create Booking", self.create_booking),
            ("List Bookings", self.list_bookings),
            ("List By Status", self.list_bookings_by_status),
            ("Search Guest Name", self.search_booking),
            ("Search by Booking ID", self.search_booking_by_id),
            ("Search By Room No", self.search_booking_by_room),
            ("Update Booking", self.update_booking),
            ("Guest Checkout", self.guest_checkout),
            ("Cancel Booking", self.cancel_booking),
        ]

        for text, command in buttons:
            btn = tk.Button(self.left_frame, text=text, 
                            command=lambda t=text, c=command: self.update_subheading(t, c),
                            width=17, font=("Helvetica", 10, "bold"), anchor="w", padx=10, 
                            bg="#e0e0e0", fg="black")  # Light Gray Background (Same as Payment Management)

            # Bind hover effects (Same as Payment Management)
            btn.bind("<Enter>", lambda e, b=btn: b.config(bg="#007BFF", fg="white"))  # Hover effect
            btn.bind("<Leave>", lambda e, b=btn: b.config(bg="#e0e0e0", fg="black"))  # Restore default

            btn.pack(pady=5, padx=10, anchor="w", fill="x")
            self.buttons.append(btn)

    def update_subheading(self, text, command):
        """Updates the subheading label and calls the selected function."""
        if hasattr(self, "subheading_label") and self.subheading_label.winfo_exists():
            self.subheading_label.config(text=text)
        else:
            self.subheading_label = tk.Label(self.right_frame, text=text, font=("Arial", 14, "bold"), bg="#f0f0f0")
            self.subheading_label.pack(pady=10)

        # Clear right frame before displaying new content
        for widget in self.right_frame.winfo_children():
            widget.destroy()

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
                entry = field_type(frame, values=["checked-in", "reservation", "complimentary"], state="readonly", font=("Arial", 11))
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

        # Label to display total booking cost (initialized empty)
        self.total_booking_cost_label = tk.Label(frame, text="", font=("Arial", 12, "bold"), fg="green", bg="#ffffff")
        self.total_booking_cost_label.pack(pady=10)


    def fetch_bookings(self, start_date_entry, end_date_entry):
        """Fetch bookings from the API and populate the table, while calculating total booking cost."""
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
                    total_booking_cost = data.get("total_booking_cost", 0)  # Get total cost from API
                else:
                    messagebox.showerror("Error", "Unexpected API response format")
                    return

                # Check if bookings list is empty
                if not bookings:
                    self.total_booking_cost_label.config(text="Total Booking Cost: $0.00")  # Reset label
                    messagebox.showinfo("No Results", "No bookings found for the selected filters.")
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
                       f"₦{float(booking.get('booking_cost', 0)) :,.2f}"

                    ))

                # Display total booking cost in green
                self.total_booking_cost_label.config(
                    text=f"Total Booking Cost: ₦{total_booking_cost:,.2f}"
                )

            else:
                messagebox.showerror("Error", response.json().get("detail", "Failed to retrieve bookings."))

        except requests.exceptions.RequestException as e:
            messagebox.showerror("Error", f"Request failed: {e}")


    def clear_right_frame(self):
        for widget in self.right_frame.winfo_children():
            widget.pack_forget()

    
    
    
    
    def list_bookings_by_status(self):
        """Displays the List Bookings by Status UI."""
        self.clear_right_frame()  # Ensure old UI elements are removed

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

        # ✅ Prevent recreation of table on every call
        if hasattr(self, "tree"):
            self.tree.destroy()

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
            print("API Response:", response.json())  # Debugging output

            if response.status_code == 200:
                data = response.json()

                # ✅ Ensure "bookings" exists before accessing it
                if "bookings" in data and data["bookings"]:
                    self.tree.delete(*self.tree.get_children())  # ✅ Clear table

                    for booking in data["bookings"]:
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
                            f"₦{float(booking.get('booking_cost', 0)) :,.2f}",  # Format booking_cost
                        ))
                else:
                    messagebox.showinfo("No Results", "No bookings found for the selected filters.")
            else:
                messagebox.showerror("Error", response.json().get("detail", "Failed to retrieve bookings."))

        except requests.exceptions.RequestException as e:
            messagebox.showerror("Error", f"Request failed: {e}")
        
            
    
    def search_booking(self):
        self.clear_right_frame()
        
        frame = tk.Frame(self.right_frame, bg="#ffffff", padx=10, pady=10)
        frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(frame, text="Search Booking by Guest Name", font=("Arial", 14, "bold"), bg="#ffffff").pack(pady=10)
        
        search_frame = tk.Frame(frame, bg="#ffffff")
        search_frame.pack(pady=5)
        
        tk.Label(search_frame, text="Guest Name:", font=("Arial", 11), bg="#ffffff").grid(row=0, column=0, padx=5, pady=5)
        self.search_entry = tk.Entry(search_frame, font=("Arial", 11))
        self.search_entry.grid(row=0, column=1, padx=5, pady=5)
        
        search_btn = ttk.Button(
            search_frame, text="Search", command=self.fetch_booking_by_guest_name
        )
        search_btn.grid(row=0, column=2, padx=10, pady=5)
        
        table_frame = tk.Frame(frame, bg="#ffffff")
        table_frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ("ID", "Room", "Guest", "Arrival", "Departure", "Status", "Number of Days", 
                "Booking Type", "Phone Number", "Booking Date", "Payment Status", "Booking Cost")
        
        self.search_tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        for col in columns:
            self.search_tree.heading(col, text=col)
            self.search_tree.column(col, width=120, anchor="center")
        
        self.search_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        y_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.search_tree.yview)
        y_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.search_tree.configure(yscroll=y_scroll.set)
        
        x_scroll = ttk.Scrollbar(frame, orient="horizontal", command=self.search_tree.xview)
        x_scroll.pack(fill=tk.X)
        self.search_tree.configure(xscroll=x_scroll.set)

    def fetch_booking_by_guest_name(self):
        guest_name = self.search_entry.get().strip()
        if not guest_name:
            messagebox.showerror("Error", "Please enter a guest name to search.")
            return
        
        api_url = "http://127.0.0.1:8000/bookings/search"
        params = {"guest_name": guest_name}
        headers = {"Authorization": f"Bearer {self.token}"}
        
        try:
            response = requests.get(api_url, params=params, headers=headers)
            if response.status_code == 200:
                data = response.json()
                bookings = data.get("bookings", [])
                
                self.search_tree.delete(*self.search_tree.get_children())
                
                for booking in bookings:
                    self.search_tree.insert("", "end", values=(
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
                        f"₦{float(booking.get('booking_cost', 0)) :,.2f}",  # Format booking_cost
                    ))
            else:
                messagebox.showerror("Error", response.json().get("detail", "No bookings found."))
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Error", f"Request failed: {e}")

    
    def search_booking_by_id(self):
        self.clear_right_frame()
        
        frame = tk.Frame(self.right_frame, bg="#ffffff", padx=10, pady=10)
        frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(frame, text="Search Booking by ID", font=("Arial", 14, "bold"), bg="#ffffff").pack(pady=10)
        
        search_frame = tk.Frame(frame, bg="#ffffff")
        search_frame.pack(pady=5)
        
        tk.Label(search_frame, text="Booking ID:", font=("Arial", 11), bg="#ffffff").grid(row=0, column=0, padx=5, pady=5)
        self.booking_id_entry = tk.Entry(search_frame, font=("Arial", 11))
        self.booking_id_entry.grid(row=0, column=1, padx=5, pady=5)
        
        search_btn = ttk.Button(
            search_frame, text="Search", command=self.fetch_booking_by_id
        )
        search_btn.grid(row=0, column=2, padx=10, pady=5)
        
        table_frame = tk.Frame(frame, bg="#ffffff")
        table_frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ("ID", "Room", "Guest", "Arrival", "Departure", "Status", "Number of Days", 
                "Booking Type", "Phone Number", "Booking Date", "Payment Status", "Booking Cost")
        
        self.search_tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        for col in columns:
            self.search_tree.heading(col, text=col)
            self.search_tree.column(col, width=120, anchor="center")
        
        self.search_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        y_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.search_tree.yview)
        y_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.search_tree.configure(yscroll=y_scroll.set)
        
        x_scroll = ttk.Scrollbar(frame, orient="horizontal", command=self.search_tree.xview)
        x_scroll.pack(fill=tk.X)
        self.search_tree.configure(xscroll=x_scroll.set)

    def fetch_booking_by_id(self):
        booking_id = self.booking_id_entry.get().strip()
    
        if not booking_id.isdigit():  # Ensure input is numeric
            messagebox.showerror("Error", "Please enter a valid numeric booking ID.")
            return
        
        try:
    
            #booking_id = int(booking_id)  # Convert to integer

            
            api_url = f"http://127.0.0.1:8000/bookings/{booking_id}"
            headers = {"Authorization": f"Bearer {self.token}"}
        
        
            response = requests.get(api_url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                booking = data.get("booking", {})
                
                # Ensure the booking details exist
                if booking:
                    self.search_tree.delete(*self.search_tree.get_children())
                    self.search_tree.insert("", "end", values=(
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
                        f"₦{float(booking.get('booking_cost', 0)) :,.2f}",  # Format booking_cost
                    ))
                else:
                    messagebox.showinfo("No Results", "No booking found with the provided ID.")
            else:
                messagebox.showerror("Error", response.json().get("detail", "No booking found."))
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Error", f"Request failed: {e}")
     

    #def search_by_room(self):
    def search_booking_by_room(self):
        self.clear_right_frame()
        
        frame = tk.Frame(self.right_frame, bg="#ffffff", padx=10, pady=10)
        frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(frame, text="Search Booking by Room Number", font=("Arial", 14, "bold"), bg="#ffffff").pack(pady=10)
        
        search_frame = tk.Frame(frame, bg="#ffffff")
        search_frame.pack(pady=5)
        
        tk.Label(search_frame, text="Room Number:", font=("Arial", 11), bg="#ffffff").grid(row=0, column=0, padx=5, pady=5)
        self.room_number_entry = tk.Entry(search_frame, font=("Arial", 11))
        self.room_number_entry.grid(row=0, column=1, padx=5, pady=5)
        
        # Date input fields
        tk.Label(search_frame, text="Start Date:", font=("Arial", 11), bg="#ffffff").grid(row=1, column=0, padx=5, pady=5)
        self.start_date_entry = DateEntry(search_frame, font=("Arial", 11), width=12, background="darkblue", foreground="white", borderwidth=2)
        self.start_date_entry.grid(row=1, column=1, padx=5, pady=5)

        tk.Label(search_frame, text="End Date:", font=("Arial", 11), bg="#ffffff").grid(row=1, column=2, padx=5, pady=5)
        self.end_date_entry = DateEntry(search_frame, font=("Arial", 11), width=12, background="darkblue", foreground="white", borderwidth=2)
        self.end_date_entry.grid(row=1, column=3, padx=5, pady=5)
        
        search_btn = ttk.Button(
            search_frame, text="Search", command=self.fetch_booking_by_room
        )
        search_btn.grid(row=2, column=0, columnspan=4, padx=10, pady=10)
        
        table_frame = tk.Frame(frame, bg="#ffffff")
        table_frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ("ID", "Room", "Guest", "Arrival", "Departure", "Status", "Number of Days", 
                "Booking Type", "Phone Number", "Booking Date", "Payment Status", "Booking Cost")
        
        self.search_tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        for col in columns:
            self.search_tree.heading(col, text=col)
            self.search_tree.column(col, width=120, anchor="center")
        
        self.search_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        y_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.search_tree.yview)
        y_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.search_tree.configure(yscroll=y_scroll.set)
        
        x_scroll = ttk.Scrollbar(frame, orient="horizontal", command=self.search_tree.xview)
        x_scroll.pack(fill=tk.X)
        self.search_tree.configure(xscroll=x_scroll.set)

    def fetch_booking_by_room(self):
        room_number = self.room_number_entry.get().strip()
        
        # Ensure room number is not empty
        if not room_number:
            messagebox.showerror("Error", "Please enter a room number.")
            return
        
        # Ensure dates are selected
        start_date = self.start_date_entry.get_date()  # Use the DateEntry widget for the start date
        end_date = self.end_date_entry.get_date()  # Use the DateEntry widget for the end date

        if not start_date or not end_date:
            messagebox.showerror("Error", "Please select both start and end dates.")
            return
        
        api_url = f"http://127.0.0.1:8000/bookings/room/{room_number}"

        # Sending the start and end dates as parameters
        params = {
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
        }
        
        headers = {"Authorization": f"Bearer {self.token}"}

        try:
            response = requests.get(api_url, params=params, headers=headers)
            print("API Response:", response.json())  # Debugging output

            if response.status_code == 200:
                data = response.json()

                # Ensure "bookings" exists before accessing it
                if "bookings" in data and data["bookings"]:
                    self.search_tree.delete(*self.search_tree.get_children())  # Clear table before inserting new data

                    for booking in data["bookings"]:
                        self.search_tree.insert("", "end", values=(
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
                            f"₦{float(booking.get('booking_cost', 0)) :,.2f}",  # Format booking_cost
                        ))
                else:
                    messagebox.showinfo("No Results", "No bookings found for the selected filters.")
            else:
                messagebox.showerror("Error", response.json().get("detail", "Failed to retrieve bookings."))

        except requests.exceptions.RequestException as e:
            messagebox.showerror("Error", f"Request failed: {e}")

    
    def update_subheading(self, text, command):
        self.subheading_label.config(text=text)
        command()

    def update_booking(self):
        self.clear_right_frame()
        frame = tk.Frame(self.right_frame, bg="#ffffff", padx=20, pady=20)
        frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(frame, text="Update Booking Form", font=("Arial", 14, "bold"), bg="#ffffff").grid(row=0, columnspan=2, pady=10)

        # Labels & Entry fields (same as create booking, with extra booking ID field)
        fields = [
            ("Booking ID", tk.Entry),
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
                entry = field_type(frame, values=["checked-in", "reservation", "complimentary"], state="readonly", font=("Arial", 11))
            elif field_type == DateEntry:
                entry = field_type(frame, font=("Arial", 11), width=12, background='darkblue', foreground='white', borderwidth=2)
            else:
                entry = field_type(frame, font=("Arial", 11), width=25)
            entry.grid(row=i+1, column=1, padx=10, pady=5)
            self.entries[label] = entry

        # Submit Button
        submit_btn = ttk.Button(frame, text="Submit Update", command=self.submit_update_booking, style="Bold.TButton")
        submit_btn.grid(row=len(fields)+1, columnspan=2, pady=10)

    def submit_update_booking(self):
        """Collects form data and sends a request to update a booking."""
        try:
            booking_data = {
                "booking_id": self.entries["Booking ID"].get(),
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

            api_url = f"http://127.0.0.1:8000/bookings/update/?booking_id={booking_data['booking_id']}"  # Adjust if needed
            headers = {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}

            response = requests.put(api_url, json=booking_data, headers=headers)

            if response.status_code == 200:
                messagebox.showinfo("Success", "Booking updated successfully!")
            else:
                messagebox.showerror("Error", response.json().get("detail", "Update failed."))

        except KeyError as e:
            messagebox.showerror("Error", f"Missing entry field: {e}")
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Error", f"Request failed: {e}")


    def update_subheading(self, text, command):
        self.subheading_label.config(text=text)
        command()

    def guest_checkout(self):
        self.clear_right_frame()
        frame = tk.Frame(self.right_frame, bg="#ffffff", padx=20, pady=20)
        frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(frame, text="Guest Checkout Form", font=("Arial", 14, "bold"), bg="#ffffff").grid(row=0, columnspan=2, pady=10)

        # Labels & Entry fields
        fields = [
            ("Room Number", tk.Entry),
        ]

        self.entries = {}
        for i, (label, field_type) in enumerate(fields):
            tk.Label(frame, text=label, font=("Arial", 11), bg="#ffffff").grid(row=i+1, column=0, sticky="w", pady=5)
            entry = field_type(frame, font=("Arial", 11), width=25)
            entry.grid(row=i+1, column=1, padx=10, pady=5)
            self.entries[label] = entry

        # Submit Button
        submit_btn = ttk.Button(frame, text="Checkout Guest", command=self.submit_guest_checkout, style="Bold.TButton")
        submit_btn.grid(row=len(fields)+1, columnspan=2, pady=10)

    def submit_guest_checkout(self):
        """Sends a request to checkout the guest by room number."""
        try:
            room_number = self.entries["Room Number"].get()

            if not room_number:  # Ensure room number is entered
                messagebox.showerror("Error", "Please enter a room number.")
                return

            api_url = f"http://127.0.0.1:8000/bookings/{room_number}/"  # Adjust API URL if necessary
            headers = {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}

            response = requests.put(api_url, headers=headers)

            if response.status_code == 200:
                messagebox.showinfo("Success", f"Guest checked out successfully for room number {room_number}!")
            else:
                messagebox.showerror("Error", response.json().get("detail", "Checkout failed."))

        except requests.exceptions.RequestException as e:
            messagebox.showerror("Error", f"Request failed: {e}") 
            
            
            
            
    def update_subheading(self, text, command):
        self.subheading_label.config(text=text)
        command()

    def cancel_booking(self):
        self.clear_right_frame()
        frame = tk.Frame(self.right_frame, bg="#ffffff", padx=20, pady=20)
        frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(frame, text="Cancel Booking Form", font=("Arial", 14, "bold"), bg="#ffffff").grid(row=0, columnspan=2, pady=10)

        # Labels & Entry fields
        fields = [
            ("Booking ID", tk.Entry),
        ]

        self.entries = {}
        for i, (label, field_type) in enumerate(fields):
            tk.Label(frame, text=label, font=("Arial", 11), bg="#ffffff").grid(row=i+1, column=0, sticky="w", pady=5)
            entry = field_type(frame, font=("Arial", 11), width=25)
            entry.grid(row=i+1, column=1, padx=10, pady=5)
            self.entries[label] = entry

        # Submit Button
        submit_btn = ttk.Button(frame, text="Cancel Booking", command=self.submit_cancel_booking, style="Bold.TButton")
        submit_btn.grid(row=len(fields)+1, columnspan=2, pady=10)

    def submit_cancel_booking(self):
        """Sends a request to cancel the booking by booking ID."""
        try:
            booking_id = self.entries["Booking ID"].get()

            if not booking_id:  # Ensure booking ID is entered
                messagebox.showerror("Error", "Please enter a booking ID.")
                return

            api_url = f"http://127.0.0.1:8000/bookings/cancel/{booking_id}/"  # Correct API URL

            headers = {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}

            response = requests.post(api_url, headers=headers)

            if response.status_code == 200:
                canceled_booking = response.json().get("canceled_booking")
                messagebox.showinfo("Success", f"Booking ID {canceled_booking['id']} has been canceled successfully!\n"
                                              f"Room Status: {canceled_booking['room_status']}\n"
                                              f"Booking Status: {canceled_booking['status']}")
            else:
                messagebox.showerror("Error", response.json().get("detail", "Cancellation failed."))

        except requests.exceptions.RequestException as e:
            messagebox.showerror("Error", f"Request failed: {e}")       
            
    
    
    
    
    def clear_right_frame(self):
        for widget in self.right_frame.winfo_children():
            widget.pack_forget()

if __name__ == "__main__":
    root = tk.Tk()
    BookingManagement(root, token="dummy_token")
    root.mainloop()
    
    
