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
            ("List Payment By Id", self.list_payment_by_id),
            ("List Void Payment", self.list_void_payment),
            ("Total Daily Payment", self.total_daily_payment),
            ("Debtor List", self.debtor_list),
            ("Void Payment", self.void_payment_by_id),
        ]

        for text, command in buttons:
            btn = tk.Button(self.left_frame, text=text, 
                            command=lambda t=text, c=command: self.update_subheading(t, c),
                            width=25, font=("Helvetica", 10, "bold"), anchor="w", padx=10)
            btn.pack(pady=5, padx=10, anchor="w", fill="x")

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
        messagebox.showinfo("Info", "List Payment Selected")

    def list_payment_by_id(self):
        messagebox.showinfo("Info", "List Payment by ID Selected")

    def list_void_payment(self):
        messagebox.showinfo("Info", "List Void Payment Selected")

    def total_daily_payment(self):
        messagebox.showinfo("Info", "Total Daily Payment Selected")

    def debtor_list(self):
        messagebox.showinfo("Info", "Debtor List Selected")

    def void_payment_by_id(self):
        messagebox.showinfo("Info", "Void Payment by ID Selected")
