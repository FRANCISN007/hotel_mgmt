import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
import requests
from utils import BASE_URL
from datetime import datetime
from datetime import datetime
import pytz

class PaymentManagement:
    def __init__(self, root, token):
        self.root = tk.Toplevel(root)
        self.root.title("Payment Management")
        self.root.geometry("900x600")
        self.token = token
        self.root.configure(bg="#f0f0f0")
        self.void_payment_tree = None  
        
        
        
        style = ttk.Style()
        style.configure("Treeview.Heading", font=("Helvetica", 12, "bold"))
        style.configure("Treeview", font=("Helvetica", 11))

        # Header Section
        self.header_frame = tk.Frame(self.root, bg="#A0A0A0", height=50)
        self.header_frame.pack(fill=tk.X)

        self.header_label = tk.Label(self.header_frame, text="Payment Management", 
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

        # Payment action buttons
        buttons = [
            ("Create Payment", self.create_payment),
            ("List Payment", self.list_payments),
            ("List Payment By ID", self.search_payment_by_id),
            ("List By Payment Status", self.list_payments_by_status),
            ("Total Daily Payment", self.list_total_daily_payments),
            ("Debtor List", self.debtor_list),
            ("Void Payment", self.void_payment),
        ]

        for text, command in buttons:
            btn = tk.Button(self.left_frame, text=text, 
                            command=lambda t=text, c=command: self.update_subheading(t, c),
                            width=17, font=("Helvetica", 10, "bold"), anchor="w", padx=10)
            btn.pack(pady=10, padx=10, anchor="w", fill="x")

    def update_subheading(self, text, command):
        """Updates the subheading label and calls the selected function."""
        if hasattr(self, "subheading_label") and self.subheading_label.winfo_exists():
            self.subheading_label.config(text=text)
        else:
            self.subheading_label = tk.Label(self.right_frame, text=text, font=("Arial", 14, "bold"), bg="#ffffff")
            self.subheading_label.pack(pady=10)

        # Clear right frame before displaying new content
        for widget in self.right_frame.winfo_children():
            widget.destroy()

        command()

    def create_payment(self):
        """Displays the create payment form inside the right frame."""
        self.subheading_label = tk.Label(self.right_frame, text="Create Payment", font=("Arial", 14, "bold"), bg="#ffffff")
        self.subheading_label.pack(pady=10)

        form_frame = tk.Frame(self.right_frame, bg="#ffffff", padx=10, pady=10)
        form_frame.pack(pady=10, padx=10, fill="both", expand=True)

        # Labels and Entry fields
        labels = ["Booking ID:", "Amount Paid:", "Discount Allowed:", "Payment Method:", "Payment Date:"]
        self.entries = {}

        for i, label_text in enumerate(labels):
            label = tk.Label(form_frame, text=label_text, font=("Helvetica", 11), bg="#ffffff")
            label.grid(row=i, column=0, sticky="w", pady=5, padx=5)

            if label_text == "Payment Date:":
                entry = DateEntry(form_frame, width=18, background="darkblue", foreground="white", borderwidth=2)
            elif label_text == "Payment Method:":
                entry = ttk.Combobox(form_frame, values=["Cash", "POS Card", "Bank Transfer"], state="readonly")
                entry.current(0)
            else:
                entry = tk.Entry(form_frame)

            entry.grid(row=i, column=1, pady=5, padx=5, sticky="ew")
            self.entries[label_text] = entry

        # Submit Button
        submit_btn = ttk.Button(form_frame, text="Submit Payment", command=self.submit_payment)
        submit_btn.grid(row=len(labels), column=0, columnspan=2, pady=15)
        
    
    
    


    def submit_payment(self):
        """Handles payment submission to the backend."""
        try:
            # Validate and fetch Booking ID
            booking_id_str = self.entries["Booking ID:"].get().strip()
            if not booking_id_str.isdigit():
                messagebox.showerror("Error", "Booking ID must be a valid integer.")
                return
            booking_id = int(booking_id_str)

            # Fetch and validate Amount Paid
            amount_paid_str = self.entries["Amount Paid:"].get().strip()
            if not amount_paid_str.replace(".", "", 1).isdigit():
                messagebox.showerror("Error", "Amount Paid must be a valid number.")
                return
            amount_paid = float(amount_paid_str)

            # Fetch and validate Discount Allowed (default to 0 if empty)
            discount_allowed_str = self.entries["Discount Allowed:"].get().strip()
            discount_allowed = float(discount_allowed_str) if discount_allowed_str.replace(".", "", 1).isdigit() else 0.0

            # Fetch Payment Method
            payment_method = self.entries["Payment Method:"].get().strip()
            if not payment_method:
                messagebox.showerror("Error", "Payment Method is required.")
                return

            # Fetch Payment Date and make it timezone-aware (set to UTC)
            payment_date = self.entries["Payment Date:"].get_date()  # get the date from the date picker
            # Convert to a datetime object and make it timezone-aware in UTC
            payment_date = datetime(payment_date.year, payment_date.month, payment_date.day, 0, 0, 0, 0)
            payment_date = pytz.utc.localize(payment_date)  # Localize to UTC

            # Convert to ISO format string (with timezone info)
            payment_date_iso = payment_date.isoformat()

            # Prepare the payload for the API request (no booking_cost)
            payload = {
                "amount_paid": amount_paid,
                "discount_allowed": discount_allowed,
                "payment_method": payment_method,
                "payment_date": payment_date_iso,  # Send the ISO formatted date with timezone
            }

            # URL for creating the payment (no need to append the booking_id here)
            url = f"http://127.0.0.1:8000/payments/{booking_id}"

            headers = {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}

            # Send the request to the API
            response = requests.post(url, json=payload, headers=headers)
            data = response.json()

            if response.status_code == 200:
                messagebox.showinfo("Success", data.get("message", "Payment created successfully!"))
            else:
                messagebox.showerror("Error", data.get("detail", "Payment failed."))

        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred: {e}")


    def list_payments(self):
        self.clear_right_frame()
        
        frame = tk.Frame(self.right_frame, bg="#ffffff", padx=10, pady=10)
        frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(frame, text="List Payments", font=("Arial", 14, "bold"), bg="#ffffff").pack(pady=10)
        
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
            text="Fetch Payments",
            command=self.fetch_payments
        )
        fetch_btn.grid(row=0, column=4, padx=10, pady=5)
        
        table_frame = tk.Frame(frame, bg="#ffffff")
        table_frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ("ID", "Guest Name", "Room Number", "Amount Paid", "Discount Allowed", "Balance Due", "Payment Method", "Payment Date", "Status", "Booking ID")
        
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120, anchor="center")
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        y_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        y_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscroll=y_scroll.set)
        
        x_scroll = ttk.Scrollbar(frame, orient="horizontal", command=self.tree.xview)
        x_scroll.pack(fill=tk.X)
        self.tree.configure(xscroll=x_scroll.set)
    
    def fetch_payments(self):
        api_url = "http://127.0.0.1:8000/payments/list"
        params = {
            "start_date": self.start_date.get_date().strftime("%Y-%m-%d"),
            "end_date": self.end_date.get_date().strftime("%Y-%m-%d"),
        }
        headers = {"Authorization": f"Bearer {self.token}"}
        
        try:
            response = requests.get(api_url, params=params, headers=headers)
            if response.status_code == 200:
                data = response.json()
                
                if isinstance(data, dict) and "payments" in data:
                    payments = data["payments"]
                elif isinstance(data, list):
                    payments = data
                else:
                    messagebox.showerror("Error", "Unexpected API response format")
                    return
                
                if not payments:
                    messagebox.showinfo("No Results", "No payments found for the selected filters.")
                    return
                
                self.tree.delete(*self.tree.get_children())
                
                for payment in payments:
                    self.tree.insert("", "end", values=(
                        payment.get("payment_id", ""),
                        payment.get("guest_name", ""),
                        payment.get("room_number", ""),
                        payment.get("amount_paid", ""),
                        payment.get("discount_allowed"),
                        payment.get("balance_due", ""),
                        payment.get("payment_method", ""),
                        payment.get("payment_date", ""),
                        payment.get("status", ""),
                        payment.get("booking_id", ""),
                    ))
            else:
                messagebox.showerror("Error", response.json().get("detail", "Failed to retrieve payments."))
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Error", f"Request failed: {e}")
    
    def clear_right_frame(self):
        for widget in self.right_frame.winfo_children():
            widget.pack_forget()
            
            
 
    def list_payments_by_status(self):
        """Displays the List Payments by Status UI."""
        self.clear_right_frame()

        frame = tk.Frame(self.right_frame, bg="#ffffff", padx=10, pady=10)
        frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(frame, text="List Payments by Status", font=("Arial", 14, "bold"), bg="#ffffff").pack(pady=10)
        
        filter_frame = tk.Frame(frame, bg="#ffffff")
        filter_frame.pack(pady=5)
        
        tk.Label(filter_frame, text="Status:", font=("Arial", 11), bg="#ffffff").grid(row=0, column=0, padx=5, pady=5)
        status_options = ["Payment Completed", "Payment Incomplete", "Voided"]
        self.payment_status_var = tk.StringVar()
        self.payment_status_var.set(status_options[0])  # Default selection
        status_menu = ttk.Combobox(filter_frame, textvariable=self.payment_status_var, values=status_options, state="readonly")
        status_menu.grid(row=0, column=1, padx=5, pady=5)
        
        tk.Label(filter_frame, text="Start Date:", font=("Arial", 11), bg="#ffffff").grid(row=0, column=2, padx=5, pady=5)
        self.payment_start_date = DateEntry(filter_frame, font=("Arial", 11))
        self.payment_start_date.grid(row=0, column=3, padx=5, pady=5)
        
        tk.Label(filter_frame, text="End Date:", font=("Arial", 11), bg="#ffffff").grid(row=0, column=4, padx=5, pady=5)
        self.payment_end_date = DateEntry(filter_frame, font=("Arial", 11))
        self.payment_end_date.grid(row=0, column=5, padx=5, pady=5)
        
        fetch_btn = ttk.Button(filter_frame, text="Fetch Payments", command=self.fetch_payments_by_status)
        fetch_btn.grid(row=0, column=6, padx=10, pady=5)
        
        # Table Frame
        table_frame = tk.Frame(frame, bg="#ffffff")
        table_frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ("ID", "Guest Name", "Room Number", "Amount Paid", "Discount", "Balance Due", "Payment Method", "Payment Date", "Status", "Booking ID")
        
        if hasattr(self, "payment_tree"):
            self.payment_tree.destroy()
        
        self.payment_tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        for col in columns:
            self.payment_tree.heading(col, text=col)
            self.payment_tree.column(col, width=120, anchor="center")
        
        self.payment_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        y_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.payment_tree.yview)
        y_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.payment_tree.configure(yscroll=y_scroll.set)
        
        x_scroll = ttk.Scrollbar(frame, orient="horizontal", command=self.payment_tree.xview)
        x_scroll.pack(fill=tk.X)
        self.payment_tree.configure(xscroll=x_scroll.set)

    def fetch_payments_by_status(self):
        """Fetch payments based on status and date filters."""
        api_url = "http://127.0.0.1:8000/payments/by-status"
        
        params = {
            "status": self.payment_status_var.get().lower(),
            "start_date": self.payment_start_date.get_date().strftime("%Y-%m-%d"),
            "end_date": self.payment_end_date.get_date().strftime("%Y-%m-%d"),
        }
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        try:
            response = requests.get(api_url, params=params, headers=headers)
            print("API Response:", response.json())  # Debugging output
        
            if response.status_code == 200:
                data = response.json()
                
                if "payments" in data and data["payments"]:
                    self.payment_tree.delete(*self.payment_tree.get_children())
                    
                    for payment in data["payments"]:
                        self.payment_tree.insert("", "end", values=(
                            payment.get("payment_id", ""),
                            payment.get("guest_name", ""),
                            payment.get("room_number", ""),
                            payment.get("amount_paid", ""),
                            payment.get("discount_allowed", ""),
                            payment.get("balance_due", ""),
                            payment.get("payment_method", ""),
                            payment.get("payment_date", ""),
                            payment.get("status", ""),
                            payment.get("booking_id", ""),
                        ))
                else:
                    messagebox.showinfo("No Results", "No payments found for the selected filters.")
            else:
                messagebox.showerror("Error", response.json().get("detail", "Failed to retrieve payments."))
        
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Error", f"Request failed: {e}")

        
   
   


    def list_total_daily_payments(self):
        self.clear_right_frame()
        
        frame = tk.Frame(self.right_frame, bg="#ffffff", padx=10, pady=10)
        frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(frame, text="Total Daily Payments", font=("Arial", 14, "bold"), bg="#ffffff").pack(pady=10)
        
        fetch_btn = ttk.Button(
            frame,
            text="Fetch Today's Payments",
            command=self.fetch_total_daily_payments
        )
        fetch_btn.pack(pady=5)
        
        self.total_label = tk.Label(frame, text="Total Amount: $0", font=("Arial", 12, "bold"), bg="#ffffff")
        self.total_label.pack(pady=5)
        
        table_frame = tk.Frame(frame, bg="#ffffff")
        table_frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ("ID", "Guest Name", "Room Number", "Amount Paid", "Discount Allowed", "Balance Due", "Payment Method", "Payment Date", "Status", "Booking ID")
        
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120, anchor="center")
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        y_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        y_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscroll=y_scroll.set)
        
        x_scroll = ttk.Scrollbar(frame, orient="horizontal", command=self.tree.xview)
        x_scroll.pack(fill=tk.X)
        self.tree.configure(xscroll=x_scroll.set)
    
    def fetch_total_daily_payments(self):
        api_url = "http://127.0.0.1:8000/payments/total_daily_payment"
        headers = {"Authorization": f"Bearer {self.token}"}
        
        try:
            response = requests.get(api_url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                
                self.total_label.config(text=f"Total Amount: ${data.get('total_amount', 0)}")
                
                if "payments" in data:
                    payments = data["payments"]
                else:
                    payments = []
                
                self.tree.delete(*self.tree.get_children())
                
                for payment in payments:
                    self.tree.insert("", "end", values=(
                        payment.get("payment_id", ""),
                        payment.get("guest_name", ""),
                        payment.get("room_number", ""),
                        payment.get("amount_paid", ""),
                        payment.get("discount allowed", ""),
                        payment.get("balance_due", ""),
                        payment.get("payment_method", ""),
                        payment.get("payment_date", ""),
                        payment.get("status", ""),
                        payment.get("booking_id", ""),
                    ))
            else:
                messagebox.showerror("Error", response.json().get("detail", "Failed to retrieve payments."))
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Error", f"Request failed: {e}")
    
    def clear_right_frame(self):
        for widget in self.right_frame.winfo_children():
            widget.pack_forget()


        

   

    def search_payment_by_id(self):
        self.clear_right_frame()

        frame = tk.Frame(self.right_frame, bg="#ffffff", padx=10, pady=10)
        frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(frame, text="Search Payment by ID", font=("Arial", 14, "bold"), bg="#ffffff").pack(pady=10)

        search_frame = tk.Frame(frame, bg="#ffffff")
        search_frame.pack(pady=5)

        tk.Label(search_frame, text="Payment ID:", font=("Arial", 11), bg="#ffffff").grid(row=0, column=0, padx=5, pady=5)
        self.payment_id_entry = tk.Entry(search_frame, font=("Arial", 11))
        self.payment_id_entry.grid(row=0, column=1, padx=5, pady=5)

        search_btn = ttk.Button(
            search_frame, text="Search", command=self.fetch_payment_by_id
        )
        search_btn.grid(row=0, column=2, padx=10, pady=5)

        table_frame = tk.Frame(frame, bg="#ffffff")
        table_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("ID", "Guest Name", "Room Number", "Amount Paid", "Discount Allowed", "Balance Due", 
                "Payment Method", "Payment Date", "Status", "Booking ID")

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

    def fetch_payment_by_id(self):
        payment_id = self.payment_id_entry.get().strip()

        if not payment_id.isdigit():  # Ensure input is numeric
            messagebox.showerror("Error", "Please enter a valid numeric payment ID.")
            return

        try:
            api_url = f"http://127.0.0.1:8000/payments/{payment_id}"
            headers = {"Authorization": f"Bearer {self.token}"}

            response = requests.get(api_url, headers=headers)

            if response.status_code == 200:
                data = response.json()

                if data:  # Ensure data exists
                    # ✅ Check if the TreeView exists before modifying it
                    if hasattr(self, "search_tree") and self.search_tree is not None:
                        self.search_tree.delete(*self.search_tree.get_children())

                        # ✅ Extract payment details from the response
                        payment_id = data.get("payment_id", "")
                        guest_name = data.get("guest_name", "")
                        room_number = data.get("room_number", "")
                        amount_paid = data.get("amount_paid", "")
                        discount_allowed = data.get("discount_allowed", "")
                        balance_due = data.get("balance_due", "")
                        payment_method = data.get("payment_method", "")
                        payment_date = data.get("payment_date", "")
                        status = data.get("status", "").lower()  # Normalize status
                        booking_id = data.get("booking_id", "")

                        # ✅ Define tag for voided payments
                        tag = "voided" if status == "voided" else "normal"

                        # ✅ Insert data into TreeView
                        self.search_tree.insert("", "end", values=(
                            payment_id, guest_name, room_number, amount_paid, 
                            discount_allowed, balance_due, payment_method, 
                            payment_date, status, booking_id
                        ), tags=(tag,))

                        # ✅ Apply color formatting
                        self.search_tree.tag_configure("voided", foreground="red")
                        self.search_tree.tag_configure("normal", foreground="black")

                    else:
                        messagebox.showerror("Error", "Payment list is not initialized.")

                else:
                    messagebox.showinfo("No Results", "No payment found with the provided ID.")
            else:
                messagebox.showerror("Error", response.json().get("detail", "No payment found."))

        except requests.exceptions.RequestException as e:
            messagebox.showerror("Error", f"Request failed: {e}")



     
     
    def void_payment(self):
        self.clear_right_frame()

        frame = tk.Frame(self.right_frame, bg="#ffffff", padx=10, pady=10)
        frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(frame, text="Void Payment", font=("Arial", 14, "bold"), bg="#ffffff").pack(pady=10)

        input_frame = tk.Frame(frame, bg="#ffffff")
        input_frame.pack(pady=5)

        tk.Label(input_frame, text="Payment ID:", font=("Arial", 11), bg="#ffffff").grid(row=0, column=0, padx=5, pady=5)
        self.payment_id_entry = tk.Entry(input_frame, font=("Arial", 11))
        self.payment_id_entry.grid(row=0, column=1, padx=5, pady=5)

        void_btn = ttk.Button(
            input_frame, text="Void Payment", command=self.process_void_payment
        )
        void_btn.grid(row=0, column=2, padx=10, pady=5)

        table_frame = tk.Frame(frame, bg="#ffffff")
        table_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("ID", "Guest Name", "Room Number", "Amount Paid", "Discount Allowed", "Balance Due", 
                    "Payment Method", "Payment Date", "Status", "Booking ID")

        self.void_payment_tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        for col in columns:
            self.void_payment_tree.heading(col, text=col)
            self.void_payment_tree.column(col, width=120, anchor="center")

        self.void_payment_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        y_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.void_payment_tree.yview)
        y_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.void_payment_tree.configure(yscroll=y_scroll.set)

        x_scroll = ttk.Scrollbar(frame, orient="horizontal", command=self.void_payment_tree.xview)
        x_scroll.pack(fill=tk.X)
        self.void_payment_tree.configure(xscroll=x_scroll.set)

    def process_void_payment(self):
        payment_id = self.payment_id_entry.get().strip()

        if not payment_id.isdigit():  # Ensure input is numeric
            messagebox.showerror("Error", "Please enter a valid numeric payment ID.")
            return

        try:
            api_url = f"http://127.0.0.1:8000/payments/void/{payment_id}"
            headers = {"Authorization": f"Bearer {self.token}"}

            response = requests.put(api_url, headers=headers)

            if response.status_code == 200:
                data = response.json()
                messagebox.showinfo("Success", data.get("message", "Payment has been voided."))
                
                # Fetch the updated payment data
                self.fetch_voided_payment_by_id(payment_id)
            else:
                messagebox.showerror("Error", response.json().get("detail", "Failed to void payment."))

        except requests.exceptions.RequestException as e:
            messagebox.showerror("Error", f"Request failed: {e}")
        
        

    def fetch_voided_payment_by_id(self, payment_id=None):
        if payment_id is None:
            payment_id = self.payment_id_entry.get().strip()

        if not payment_id.isdigit():  # Ensure input is numeric
            messagebox.showerror("Error", "Please enter a valid numeric payment ID.")
            return

        try:
            api_url = f"http://127.0.0.1:8000/payments/{payment_id}"
            headers = {"Authorization": f"Bearer {self.token}"}

            response = requests.get(api_url, headers=headers)

            if response.status_code == 200:
                data = response.json()

                if data:  # Ensure data exists
                    if hasattr(self, "void_payment_tree") and self.void_payment_tree is not None:
                        self.void_payment_tree.delete(*self.void_payment_tree.get_children())  

                    # Insert payment details
                    self.void_payment_tree.insert("", "end", values=(
                        data.get("payment_id", ""),
                        data.get("guest_name", ""),
                        data.get("room_number", ""),
                        data.get("amount_paid", ""),
                        data.get("discount_allowed", ""),
                        data.get("balance_due", ""),
                        data.get("payment_method", ""),
                        data.get("payment_date", ""),
                        data.get("status", ""),
                        data.get("booking_id", ""),
                    ))
                else:
                    messagebox.showinfo("No Results", "No payment found with the provided ID.")
            else:
                messagebox.showerror("Error", response.json().get("detail", "No payment found."))

        except requests.exceptions.RequestException as e:
            messagebox.showerror("Error", f"Request failed: {e}")

    
        

    #def list_payments(self):
        #messagebox.showinfo("Info", "List Payment Selected")

    #def list_payment_by_id(self):
        #messagebox.showinfo("Info", "List Payment by ID Selected")

    #def list_by_payment_status(self):
        #messagebox.showinfo("Info", "List Void Payment Selected")

    #def total_daily_payment(self):
        #messagebox.showinfo("Info", "Total Daily Payment Selected")

    def debtor_list(self):
        messagebox.showinfo("Info", "Debtor List Selected")

    #def void_payment(self):
        #messagebox.showinfo("Info", "Void Payment by ID Selected")
