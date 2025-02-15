import tkinter as tk
from tkinter import ttk, messagebox
import requests
from utils import BASE_URL
from tkcalendar import DateEntry

from utils import export_to_excel, print_excel
import os
import pandas as pd


class EventManagement:
    def __init__(self, root, token):
        self.root = tk.Toplevel(root)
        self.root.title("Event Management")
        self.token = token
        self.root.configure(bg="#f0f0f0")
        self.username = "current_user"

        # Get screen width and height
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        window_width = 1200
        window_height = 600
        x_position = (screen_width - window_width) // 2
        y_position = (screen_height - window_height) // 2
        self.root.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")

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
        separator = tk.Frame(self.left_frame, height=4, bg="#333333")
        separator.pack(fill="x", padx=5, pady=10)
        
        # Event Payment action buttons
        payment_buttons = [
            ("➕Create Event Payment", self.create_event_payment),
            ("📑List Event Payments", self.list_events_payment),
            ("📑List Payment By Status", self.list_payment_by_status),
            ("🔎Search by Payment ID", self.search_payment_by_id),
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
            
        self.export_button = tk.Button(self.header_frame, text="Export to Excel", 
                               command=self.export_report, bg="#007BFF", fg="white", font=("Helvetica", 10, "bold"))
        self.export_button.pack(side=tk.RIGHT, padx=10, pady=5)

        self.print_button = tk.Button(self.header_frame, text="Print Report", 
                              command=self.print_report, bg="#28A745", fg="white", font=("Helvetica", 10, "bold"))
        self.print_button.pack(side=tk.RIGHT, padx=10, pady=5)        

    def update_subheading(self, text, command):
        self.subheading_label.config(text=text)
        command()
     
    def export_report(self):
        """Export only the visible bookings from the Treeview to Excel"""
        if not hasattr(self, "tree") or not self.tree.get_children():
            messagebox.showwarning("Warning", "No data available to export.")
            return

        # Extract column headers
        columns = [self.tree.heading(col)["text"] for col in self.tree["columns"]]

        # Extract row data from Treeview
        rows = []
        for item in self.tree.get_children():
            row_data = [self.tree.item(item)["values"][i] for i in range(len(columns))]
            rows.append(row_data)

        # Convert to DataFrame for better formatting
        df = pd.DataFrame(rows, columns=columns)

        # Save in user's Downloads folder
        download_dir = os.path.join(os.path.expanduser("~"), "Downloads")
        file_path = os.path.join(download_dir, "event_report.xlsx")

        try:
            df.to_excel(file_path, index=False)  # Export properly formatted Excel
            self.last_exported_file = file_path
            messagebox.showinfo("Success", f"Report exported successfully!\nSaved at: {file_path}")
        except PermissionError:
            messagebox.showerror("Error", "Permission denied! Close the file if it's open and try again.")
        except Exception as e:
            messagebox.showerror("Error", f"Error exporting to Excel: {e}")


    def print_report(self):
        """Print the exported Excel report"""
        if hasattr(self, 'last_exported_file') and self.last_exported_file:
            print_excel(self.last_exported_file)
        else:
            messagebox.showwarning("Warning", "Please export the report before printing.")

     

        
    def create_event(self):
        self.clear_right_frame()
        frame = tk.Frame(self.right_frame, bg="#ffffff", padx=20, pady=20)
        frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(frame, text="Create Event Form", font=("Arial", 14, "bold"), bg="#ffffff").grid(row=0, columnspan=2, pady=10)

        # Labels & Entry fields
        fields = [
            ("Organizer", tk.Entry),
            ("Title", tk.Entry),
            ("Description", tk.Text),
            ("Start Date", DateEntry),
            ("End Date", DateEntry),
            ("Event Amount", tk.Entry),
            ("Caution Fee", tk.Entry),
            ("Location", tk.Entry),
            ("Phone Number", tk.Entry),
            ("Address", tk.Entry),
        ]

        self.entries = {}
        for i, (label, field_type) in enumerate(fields):
            tk.Label(frame, text=label, font=("Arial", 12), bg="#ffffff").grid(row=i+1, column=0, sticky="w", pady=5)
            
            if field_type == tk.Text:
                entry = field_type(frame, font=("Arial", 12), width=30, height=3)
            elif field_type == DateEntry:
                entry = field_type(frame, font=("Arial", 12), width=12, background='darkblue', foreground='white', borderwidth=2)
            else:
                entry = field_type(frame, font=("Arial", 12), width=25)
            
            entry.grid(row=i+1, column=1, padx=10, pady=5)
            self.entries[label] = entry

        # Submit Button
        submit_btn = ttk.Button(frame, text="Submit Event", command=self.submit_event, style="Bold.TButton")
        submit_btn.grid(row=len(fields)+1, columnspan=2, pady=10)

    def submit_event(self):
        """Collects form data and sends a request to create an event."""
        try:
            created_by = self.username  # Ensure this is properly initialized
            
            event_data = {
                "organizer": self.entries["Organizer"].get(),
                "title": self.entries["Title"].get(),
                "description": self.entries["Description"].get("1.0", "end-1c"),  
                "start_datetime": self.entries["Start Date"].get_date().strftime("%Y-%m-%d"),
                "end_datetime": self.entries["End Date"].get_date().strftime("%Y-%m-%d"),
                "event_amount": self.entries["Event Amount"].get(),
                "caution_fee": self.entries["Caution Fee"].get(),
                "location": self.entries["Location"].get(),
                "phone_number": self.entries["Phone Number"].get(),
                "address": self.entries["Address"].get(),
                "payment_status": "active",
                "created_by": created_by,  # Ensure username is available
            }

            if not all(event_data.values()):  # Ensure all fields are filled
                messagebox.showerror("Error", "Please fill in all fields")
                return

            api_url = "http://127.0.0.1:8000/events/"  # Adjust if needed
            headers = {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}

            response = requests.post(api_url, json=event_data, headers=headers)

            if response.status_code == 200:
                response_data = response.json()
                event_id = response_data.get("id")  # Extract event ID

                if event_id:
                    messagebox.showinfo("Success", f"Event created successfully!\nEvent ID: {event_id}")
                else:
                    messagebox.showerror("Error", "Event ID missing in response.")

            else:
                messagebox.showerror("Error", response.json().get("detail", "Event creation failed."))

        except KeyError as e:
            messagebox.showerror("Error", f"Missing entry field: {e}")
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Error", f"Request failed: {e}")

    def clear_right_frame(self):
        """Clears the right frame before displaying new content."""
        for widget in self.right_frame.winfo_children():
            widget.destroy()
   
        
    
    
    def list_events(self):
        """List events with filtering by date."""
        self.clear_right_frame()

        frame = tk.Frame(self.right_frame, bg="#ffffff", padx=10, pady=10)
        frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(frame, text="📅 List Events", font=("Arial", 14, "bold"), bg="#ffffff").pack(pady=10)

        # ---------------- Filter Section ---------------- #
        filter_frame = tk.Frame(frame, bg="#ffffff")
        filter_frame.pack(pady=5)

        tk.Label(filter_frame, text="Start Date:", font=("Arial", 11), bg="#ffffff").grid(row=0, column=0, padx=5, pady=5)
        self.start_date = DateEntry(filter_frame, font=("Arial", 11))
        self.start_date.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(filter_frame, text="End Date:", font=("Arial", 11), bg="#ffffff").grid(row=0, column=2, padx=5, pady=5)
        self.end_date = DateEntry(filter_frame, font=("Arial", 11))
        self.end_date.grid(row=0, column=3, padx=5, pady=5)

        fetch_btn = ttk.Button(filter_frame, text="🔍 Fetch Events", command=lambda: self.fetch_events(self.start_date, self.end_date))
        fetch_btn.grid(row=0, column=4, padx=10, pady=5)

        # ---------------- Event Table ---------------- #
        table_frame = tk.Frame(frame, bg="#ffffff")
        table_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("ID", "Organizer", "Title", "Event_Amount", "Caution_Fee", "Start Date", "End Date", "Location", "Phone", "Status", "created_by")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings")

        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=140, anchor="center")

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Scrollbars
        y_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        y_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscroll=y_scroll.set)

        x_scroll = ttk.Scrollbar(frame, orient="horizontal", command=self.tree.xview)
        x_scroll.pack(fill=tk.X)
        self.tree.configure(xscroll=x_scroll.set)

        # Total Amount Label
        self.total_label = tk.Label(frame, text="Total Event Amount: ₦0.00", font=("Arial", 12, "bold"), bg="#ffffff", fg="blue")
        self.total_label.pack(pady=10)

    def fetch_events(self, start_date_entry, end_date_entry):
        """Fetch events from API and populate the table."""
        api_url = "http://127.0.0.1:8000/events"
        params = {
            "start_date": start_date_entry.get_date().strftime("%Y-%m-%d"),
            "end_date": end_date_entry.get_date().strftime("%Y-%m-%d"),
        }
        headers = {"Authorization": f"Bearer {self.token}"}

        try:
            response = requests.get(api_url, params=params, headers=headers)
            if response.status_code == 200:
                events = response.json()
                self.tree.delete(*self.tree.get_children())  # Clear table
                total_amount = 0

                for event in events:
                    event_amount = float(event.get("event_amount", 0))
                    total_amount += event_amount
                    self.tree.insert("", "end", values=(
                        event.get("id", ""),
                        event.get("organizer", ""),
                        event.get("title", ""),
                        f"₦{event_amount:,.2f}",
                        f"₦{float(event.get('caution_fee', 0)) :,.2f}",
                        event.get("start_datetime", ""),
                        event.get("end_datetime", ""),
                        event.get("location", ""),
                        event.get("phone_number", ""),
                        event.get("payment_status", ""),
                        event.get("created_by", ""),
                    ))

                self.total_label.config(text=f"Total Event Amount: ₦{total_amount:,.2f}")

                if not events:
                    messagebox.showinfo("No Results", "No events found for the selected filters.")
                    self.total_label.config(text="Total Event Amount: ₦0.00")

            else:
                messagebox.showerror("Error", response.json().get("detail", "Failed to retrieve events."))

        except requests.exceptions.RequestException as e:
            messagebox.showerror("Error", f"Request failed: {e}")

    def clear_right_frame(self):
        """Clears the right frame before rendering new content."""
        for widget in self.right_frame.winfo_children():
            widget.pack_forget()



    
    
    def search_event_by_id(self):
        self.clear_right_frame()
        
        frame = tk.Frame(self.right_frame, bg="#ffffff", padx=10, pady=10)
        frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(frame, text="Search Event by ID", font=("Arial", 14, "bold"), bg="#ffffff").pack(pady=10)
        
        search_frame = tk.Frame(frame, bg="#ffffff")
        search_frame.pack(pady=5)
        
        tk.Label(search_frame, text="Event ID:", font=("Arial", 11), bg="#ffffff").grid(row=0, column=0, padx=5, pady=5)
        self.event_id_entry = tk.Entry(search_frame, font=("Arial", 11))
        self.event_id_entry.grid(row=0, column=1, padx=5, pady=5)
        
        search_btn = ttk.Button(
            search_frame, text="Search", command=self.fetch_event_by_id
        )
        search_btn.grid(row=0, column=2, padx=10, pady=5)
        
        table_frame = tk.Frame(frame, bg="#ffffff")
        table_frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ("ID", "Organizer", "Title", "Event_Amount", "Caution_Fee", "Start Date", "End Date", 
                "Location", "Phone Number", "Payment Status", "Created_by")

        self.search_tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        for col in columns:
            self.search_tree.heading(col, text=col)
            self.search_tree.column(col, width=140, anchor="center")
        
        self.search_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        y_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.search_tree.yview)
        y_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.search_tree.configure(yscroll=y_scroll.set)
        
        x_scroll = ttk.Scrollbar(frame, orient="horizontal", command=self.search_tree.xview)
        x_scroll.pack(fill=tk.X)
        self.search_tree.configure(xscroll=x_scroll.set)

    def fetch_event_by_id(self):
        event_id = self.event_id_entry.get().strip()

        if not event_id.isdigit():  # Ensure input is numeric
            messagebox.showerror("Error", "Please enter a valid numeric event ID.")
            return
        
        try:
            api_url = f"http://127.0.0.1:8000/events/{event_id}"
            headers = {"Authorization": f"Bearer {self.token}"}
        
            response = requests.get(api_url, headers=headers)
            if response.status_code == 200:
                event = response.json()
                
                # Ensure the event details exist
                if event:
                    self.search_tree.delete(*self.search_tree.get_children())
                    self.search_tree.insert("", "end", values=(
                        event.get("id", ""),
                        event.get("organizer", ""),
                        event.get("title", ""),
                        #f"₦{float(booking.get('booking_cost', 0)) :,.2f}",
                        f"₦{float(event.get('event_amount', 0)) :,.2f}",
                        f"₦{float(event.get('caution_fee', 0)) :,.2f}",
                        event.get("start_datetime", ""),
                        event.get("end_datetime", ""),
                        event.get("location", ""),
                        event.get("phone_number", ""),
                        event.get("payment_status", ""),
                        event.get("created_by", ""),
                    ))
                else:
                    messagebox.showinfo("No Results", "No event found with the provided ID.")
            else:
                messagebox.showerror("Error", response.json().get("detail", "No event found."))
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Error", f"Request failed: {e}")
  
        
        
        
    def update_event(self):
        """Creates a form to update an event."""
        self.clear_right_frame()
        frame = tk.Frame(self.right_frame, bg="#ffffff", padx=20, pady=20)
        frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(frame, text="Update Event Form", font=("Arial", 14, "bold"), bg="#ffffff").grid(row=0, columnspan=2, pady=10)

        # Labels & Entry fields (based on Create Event fields)
        fields = [
            ("Event ID", tk.Entry),
            ("Organizer", tk.Entry),
            ("Title", tk.Entry),
            ("Description", tk.Entry),
            ("Location", tk.Entry),
            ("Phone Number", tk.Entry),
            ("Address", tk.Entry),
            ("Start Date", DateEntry),
            ("End Date", DateEntry),
            ("Event Amount", tk.Entry),
            ("Caution Fee", tk.Entry),
            ("Payment Status", ttk.Combobox)
        ]

        self.entries = {}
        for i, (label, field_type) in enumerate(fields):
            tk.Label(frame, text=label, font=("Arial", 11), bg="#ffffff").grid(row=i+1, column=0, sticky="w", pady=5)
            if field_type == ttk.Combobox:
                entry = field_type(frame, values=["pending", "complete", "incomplete", "cancelled"], state="readonly", font=("Arial", 11))
            elif field_type == DateEntry:
                entry = field_type(frame, font=("Arial", 11), width=12, background='darkblue', foreground='white', borderwidth=2)
            else:
                entry = field_type(frame, font=("Arial", 11), width=25)
            entry.grid(row=i+1, column=1, padx=10, pady=5)
            self.entries[label] = entry

        # Submit Button
        submit_btn = ttk.Button(frame, text="Submit Update", command=self.submit_update_event, style="Bold.TButton")
        submit_btn.grid(row=len(fields)+1, columnspan=2, pady=10)

    def submit_update_event(self):
        """Collects form data and sends a request to update an event."""
        try:
            event_data = {
                "organizer": self.entries["Organizer"].get(),
                "title": self.entries["Title"].get(),
                "description": self.entries["Description"].get(),
                "location": self.entries["Location"].get(),
                "phone_number": self.entries["Phone Number"].get(),
                "address": self.entries["Address"].get(),
                "start_datetime": self.entries["Start Date"].get_date().strftime("%Y-%m-%d"),
                "end_datetime": self.entries["End Date"].get_date().strftime("%Y-%m-%d"),
                "event_amount": float(self.entries["Event Amount"].get() or 0),
                "caution_fee": float(self.entries["Caution Fee"].get() or 0),
                "payment_status": self.entries["Payment Status"].get(),
            }

            event_id = self.entries["Event ID"].get()
            if not event_id or not all(event_data.values()):  # Ensure all fields are filled
                messagebox.showerror("Error", "Please fill in all fields")
                return

            api_url = f"http://127.0.0.1:8000/events/{event_id}"
            headers = {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}

            response = requests.put(api_url, json=event_data, headers=headers)

            if response.status_code == 200:
                messagebox.showinfo("Success", "Event updated successfully!")
            else:
                messagebox.showerror("Error", response.json().get("detail", "Update failed."))

        except KeyError as e:
            messagebox.showerror("Error", f"Missing entry field: {e}")
        except ValueError:
            messagebox.showerror("Error", "Invalid numeric input for Event Amount or Caution Fee.")
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Error", f"Request failed: {e}")

    def update_subheading(self, text, command):
        self.subheading_label.config(text=text)
        command()   
        
      
    def cancel_event(self):
        """Creates a form to cancel an event."""
        self.clear_right_frame()
        frame = tk.Frame(self.right_frame, bg="#ffffff", padx=20, pady=20)
        frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(frame, text="Cancel Event Form", font=("Arial", 14, "bold"), bg="#ffffff").grid(row=0, columnspan=2, pady=10)

        # Labels & Entry fields
        fields = [
            ("Event ID", tk.Entry),
            ("Cancellation Reason (Required)", tk.Entry),
        ]

        self.entries = {}
        for i, (label, field_type) in enumerate(fields):
            tk.Label(frame, text=label, font=("Arial", 11), bg="#ffffff").grid(row=i+1, column=0, sticky="w", pady=5)
            entry = field_type(frame, font=("Arial", 11), width=25)
            entry.grid(row=i+1, column=1, padx=10, pady=5)
            self.entries[label] = entry

        # Submit Button
        submit_btn = ttk.Button(frame, text="Cancel Event", command=self.submit_cancel_event, style="Bold.TButton")
        submit_btn.grid(row=len(fields)+1, columnspan=2, pady=10)

    def cancel_event(self):
        """Create a UI form to cancel an event."""
        self.clear_right_frame()
        frame = tk.Frame(self.right_frame, bg="#ffffff", padx=20, pady=20)
        frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(frame, text="Cancel Event Form", font=("Arial", 14, "bold"), bg="#ffffff").grid(row=0, columnspan=2, pady=10)

        # Labels & Entry fields
        fields = [
            ("Event ID", tk.Entry),
            ("Cancellation Reason", tk.Entry),  # Ensure this key matches what is used in submit_cancel_event
        ]

        self.entries = {}
        for i, (label, field_type) in enumerate(fields):
            tk.Label(frame, text=label, font=("Arial", 11), bg="#ffffff").grid(row=i+1, column=0, sticky="w", pady=5)
            entry = field_type(frame, font=("Arial", 11), width=25)
            entry.grid(row=i+1, column=1, padx=10, pady=5)
            self.entries[label] = entry  # Ensure the exact key name is used

        # Submit Button
        submit_btn = ttk.Button(frame, text="Cancel Event", command=self.submit_cancel_event, style="Bold.TButton")
        submit_btn.grid(row=len(fields)+1, columnspan=2, pady=10)

        
    def submit_cancel_event(self):
        """Sends a request to cancel an event by event ID, including the cancellation reason."""
        try:
            event_id = self.entries["Event ID"].get().strip()  # Ensure input is stripped
            cancellation_reason = self.entries["Cancellation Reason"].get().strip()  # Ensure proper retrieval

            if not event_id:
                messagebox.showerror("Error", "Please enter an Event ID.")
                return

            if not cancellation_reason:
                messagebox.showerror("Error", "Cancellation reason is required.")
                return

            # Construct the API URL with cancellation reason as a query parameter
            api_url = f"http://127.0.0.1:8000/events/{event_id}/cancel?cancellation_reason={requests.utils.quote(cancellation_reason)}"

            headers = {"Authorization": f"Bearer {self.token}"}

            # Send PUT request without JSON body since params are in the URL
            response = requests.put(api_url, headers=headers)

            if response.status_code == 200:
                messagebox.showinfo("Success", f"Event ID {event_id} has been successfully canceled!\n"
                                            f"Cancellation Reason: {cancellation_reason}")
            else:
                messagebox.showerror("Error", response.json().get("detail", "Cancellation failed."))

        except KeyError as e:
            messagebox.showerror("Error", f"Missing entry field: {e}")  # Handle missing key errors
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Error", f"Request failed: {e}")

                
        
    def create_event_payment(self):
        """Displays the create event payment form inside the right frame."""
        self.clear_right_frame()  # Clear previous content

        frame = tk.Frame(self.right_frame, bg="#ffffff", padx=20, pady=20)
        frame.pack(fill=tk.BOTH, expand=True)

        # Create subheading label
        tk.Label(frame, text="Create Event Payment", font=("Arial", 14, "bold"), bg="#ffffff").grid(row=0, columnspan=2, pady=10)

        # Form frame
        form_frame = tk.Frame(frame, bg="#ffffff", padx=10, pady=10)
        form_frame.grid(row=1, columnspan=2, pady=10, padx=10, sticky="ew")

        # Labels and Entry fields
        labels = ["Event ID:", "Organiser Name:", "Amount Paid:", "Discount Allowed:", "Payment Method:"]
        self.entries = {}

        for i, label_text in enumerate(labels):
            label = tk.Label(form_frame, text=label_text, font=("Helvetica", 12), bg="#ffffff")
            label.grid(row=i, column=0, sticky="w", pady=5, padx=5)

            if label_text == "Payment Method:":
                entry = ttk.Combobox(form_frame, values=["Cash", "POS Card", "Bank Transfer"], state="readonly")
                entry.current(0)
            else:
                entry = tk.Entry(form_frame)

            entry.grid(row=i, column=1, pady=5, padx=5, sticky="ew")
            self.entries[label_text] = entry

        # Submit Button
        submit_btn = ttk.Button(form_frame, text="Submit Payment", command=self.submit_event_payment)
        submit_btn.grid(row=len(labels), column=0, columnspan=2, pady=15)


    def submit_event_payment(self):
        """Handles submission of event payment to backend."""
        try:
            # Validate and fetch Event ID
            event_id_str = self.entries["Event ID:"].get().strip()
            if not event_id_str.isdigit():
                messagebox.showerror("Error", "Event ID must be a valid integer.")
                return
            event_id = int(event_id_str)

            # Fetch and validate Organiser Name
            organiser = self.entries["Organiser Name:"].get().strip()
            if not organiser:
                messagebox.showerror("Error", "Organiser name is required.")
                return

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

            # Prepare API payload
            payload = {
                "event_id": event_id,
                "organiser": organiser,
                "amount_paid": amount_paid,
                "discount_allowed": discount_allowed,
                "payment_method": payment_method,
                "created_by": self.username  # Ensure `self.username` holds the correct username
            }

            # API URL for creating event payment
            url = "http://127.0.0.1:8000/eventpayment/"
            headers = {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}

            # Send request to API
            response = requests.post(url, json=payload, headers=headers)
            data = response.json()

            if response.status_code == 200:
                messagebox.showinfo("Success", f"Event Payment successful!\nEvent ID: {event_id}\nOrganiser: {organiser}")
            else:
                messagebox.showerror("Error", data.get("detail", "Payment failed."))
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred: {e}")


    
    def list_events_payment(self):
        self.clear_right_frame()
        
        frame = tk.Frame(self.right_frame, bg="#ffffff", padx=10, pady=10)
        frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(frame, text="List Event Payments", font=("Arial", 14, "bold"), bg="#ffffff").pack(pady=10)

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
            command=lambda: self.fetch_event_payments(self.start_date, self.end_date)
        )
        fetch_btn.grid(row=0, column=4, padx=10, pady=5)

        table_frame = tk.Frame(frame, bg="#ffffff")
        table_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("Payment ID", "Event ID", "Organiser", "Event Amount", "Amount Paid", "Discount Allowed", 
                   "Balance Due", "Payment Method", "Payment Status", "Payment Date", "Created By")

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

        self.total_payment_label = tk.Label(frame, text="", font=("Arial", 12, "bold"), bg="#ffffff", fg="blue")
        self.total_payment_label.pack(pady=10)

    def fetch_event_payments(self, start_date_entry, end_date_entry):
        api_url = "http://127.0.0.1:8000/eventpayment/"  
        params = {
            "start_date": start_date_entry.get_date().strftime("%Y-%m-%d"),
            "end_date": end_date_entry.get_date().strftime("%Y-%m-%d"),
        }
        headers = {"Authorization": f"Bearer {self.token}"}

        try:
            response = requests.get(api_url, params=params, headers=headers)
            if response.status_code == 200:
                data = response.json()
                
                if not isinstance(data, list):
                    messagebox.showerror("Error", "Unexpected API response format")
                    return
                
                if not data:
                    self.total_payment_label.config(text="Total Payments: ₦0.00")
                    messagebox.showinfo("No Results", "No payments found for the selected filters.")
                    return
                
                self.tree.delete(*self.tree.get_children())
                total_amount_paid = 0
                
                for payment in data:
                    if payment.get("payment_status", "").lower() == "voided":
                        continue  # Exclude voided payments
                    
                    total_amount_paid += float(payment.get("amount_paid", 0))
                    
                    self.tree.insert("", "end", values=(
                        payment.get("id", ""),
                        payment.get("event_id", ""),
                        payment.get("organiser", ""),
                        f"₦{float(payment.get('event_amount', 0)) :,.2f}",
                        f"₦{float(payment.get('amount_paid', 0)) :,.2f}",
                        f"₦{float(payment.get('discount_allowed', 0)) :,.2f}",
                        f"₦{float(payment.get('balance_due', 0)) :,.2f}",
                        payment.get("payment_method", ""),
                        payment.get("payment_status", ""),
                        payment.get("payment_date", ""),
                        payment.get("created_by", ""),
                    ))
                
                self.total_payment_label.config(
                    text=f"Total Payments: ₦{total_amount_paid:,.2f}"
                )
            else:
                messagebox.showerror("Error", response.json().get("detail", "Failed to retrieve payments."))

        except requests.exceptions.RequestException as e:
            messagebox.showerror("Error", f"Request failed: {e}")

    def clear_right_frame(self):
        for widget in self.right_frame.winfo_children():
            widget.pack_forget()




    def list_payment_by_status(self):
        """Displays the List Payments by Status UI."""
        self.clear_right_frame()  # Ensure old UI elements are removed

        # Create a new frame for the table with scrollable functionality
        frame = tk.Frame(self.right_frame, bg="#ffffff", padx=10, pady=10)
        frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(frame, text="List Payments by Status", font=("Arial", 14, "bold"), bg="#ffffff").pack(pady=10)

        # Filter Frame
        filter_frame = tk.Frame(frame, bg="#ffffff")
        filter_frame.pack(pady=5)

        # Status Dropdown
        tk.Label(filter_frame, text="Status:", font=("Arial", 11), bg="#ffffff").grid(row=0, column=0, padx=5, pady=5)

        status_options = ["pending", "complete", "incomplete", "void"]
        self.status_var = tk.StringVar(value=status_options[0])  # Default selection

        status_menu = ttk.Combobox(filter_frame, textvariable=self.status_var, values=status_options, state="readonly")
        status_menu.grid(row=0, column=1, padx=5, pady=5)
        #status_menu.bind("<<ComboboxSelected>>", lambda event: self.status_var.set(status_menu.get()))
        
        # Bind the selection event to a function that updates self.status_var
        def on_status_change(event):
            #print("Selected Status:", self.status_var.get())  # Debugging: Check what is selected
            self.status_var.set(status_menu.get())  # Ensure value updates

        status_menu.bind("<<ComboboxSelected>>", on_status_change)  # Event binding

        # Start Date
        tk.Label(filter_frame, text="Start Date:", font=("Arial", 11), bg="#ffffff").grid(row=0, column=2, padx=5, pady=5)
        self.start_date = DateEntry(filter_frame, font=("Arial", 11))
        self.start_date.grid(row=0, column=3, padx=5, pady=5)

        # End Date
        tk.Label(filter_frame, text="End Date:", font=("Arial", 11), bg="#ffffff").grid(row=0, column=4, padx=5, pady=5)
        self.end_date = DateEntry(filter_frame, font=("Arial", 11))
        self.end_date.grid(row=0, column=5, padx=5, pady=5)

        # Fetch Button
        fetch_btn = ttk.Button(filter_frame, text="Fetch Payments", command=self.fetch_payments_by_status)
        fetch_btn.grid(row=0, column=6, padx=10, pady=5)

        

        # Table Frame
        table_frame = tk.Frame(frame, bg="#ffffff")
        table_frame.pack(fill=tk.BOTH, expand=True)
        
        # Total Payment Amount Label
        self.total_cost_label = tk.Label(frame, text="Total Payment Amount: ₦0.00", 
                                 font=("Arial", 12, "bold"), bg="#ffffff", fg="blue")
        self.total_cost_label.pack(pady=5)

        

        columns = ("Payment ID", "Event ID", "Organiser Name", "Event Amount", "Amount Paid", "Discount Allowed", "Balance Due", "Payment Date", "Status", "Payment Method", "Created By")
        
        if hasattr(self, "tree"):
            self.tree.destroy()

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


    def fetch_payments_by_status(self):
        """Fetch payments based on status and date filters."""
        api_url = "http://127.0.0.1:8000/eventpayment/status"

        # Ensure only valid query parameters are sent
        params = {
            "status": self.status_var.get().strip().lower(),
            "start_date": self.start_date.get_date().strftime("%Y-%m-%d"),
            "end_date": self.end_date.get_date().strftime("%Y-%m-%d"),
        }

        headers = {"Authorization": f"Bearer {self.token}"}

        try:
            response = requests.get(api_url, params=params, headers=headers)
            data = response.json()

            if response.status_code == 200:
                self.tree.delete(*self.tree.get_children())  # Clear existing table data
                total_amount = 0

                if isinstance(data, list):  # Ensure response is a list
                    for payment in data:
                        # Extract values safely
                        event_amount = float(payment.get("event_amount", 0))
                        amount_paid = float(payment.get("amount_paid", 0))  # <-- Update to amount_paid
                        discount_allowed = float(payment.get("discount_allowed", 0))
                        balance_due = float(payment.get("balance_due", 0))

                        total_amount += amount_paid  # Sum total amount paid

                        # Insert data into table
                        self.tree.insert("", "end", values=(
                            payment.get("id", ""),
                            payment.get("event_id", ""),
                            payment.get("organiser", ""),
                            f"₦{event_amount:,.2f}",
                            f"₦{amount_paid:,.2f}",
                            f"₦{discount_allowed:,.2f}",
                            f"₦{balance_due:,.2f}",
                            payment.get("payment_date", ""),
                            payment.get("payment_status", ""),
                            payment.get("payment_method", ""),
                            payment.get("created_by", ""),
                        ))

                    # Update Total Payment Label
                    self.total_cost_label.config(text=f"Total Payment Amount: ₦{total_amount:,.2f}")
                else:
                    messagebox.showinfo("No Results", "No payments found for the selected filters.")
            else:
                messagebox.showerror("Error", data.get("detail", "Failed to retrieve payments."))

        except requests.exceptions.RequestException as e:
            messagebox.showerror("Error", f"Request failed: {e}")
            
            
            


    def search_payment_by_id(self):
        """GUI for searching a payment by ID."""
        self.clear_right_frame()

        frame = tk.Frame(self.right_frame, bg="#ffffff", padx=10, pady=10)
        frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(frame, text="Search Payment by ID", font=("Arial", 14, "bold"), bg="#ffffff").pack(pady=10)

        # Search Input Frame
        search_frame = tk.Frame(frame, bg="#ffffff")
        search_frame.pack(pady=5)

        tk.Label(search_frame, text="Payment ID:", font=("Arial", 11), bg="#ffffff").grid(row=0, column=0, padx=5, pady=5)
        self.payment_id_entry = tk.Entry(search_frame, font=("Arial", 11))
        self.payment_id_entry.grid(row=0, column=1, padx=5, pady=5)

        search_btn = ttk.Button(
            search_frame, text="Search", command=self.fetch_payment_by_id
        )
        search_btn.grid(row=0, column=2, padx=10, pady=5)

        # Table Frame
        table_frame = tk.Frame(frame, bg="#ffffff")
        table_frame.pack(fill=tk.BOTH, expand=True)

        columns = (
            "ID", "Event ID", "Organiser", "Event Amount", "Amount Paid", 
            "Discount Allowed", "Balance Due", "Payment Method", "Status", 
            "Payment Date", "Created By"
        )

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
        """Fetch and display payment details by ID."""
        payment_id = self.payment_id_entry.get().strip()

        if not payment_id.isdigit():
            messagebox.showerror("Error", "Please enter a valid numeric payment ID.")
            return

        try:
            api_url = f"http://127.0.0.1:8000/eventpayment/{payment_id}"
            headers = {"Authorization": f"Bearer {self.token}"}

            response = requests.get(api_url, headers=headers)
            if response.status_code == 200:
                payment = response.json()

                if payment:
                    self.search_tree.delete(*self.search_tree.get_children())

                    # Format amounts
                    event_amount = f"₦{float(payment.get('event_amount', 0)) :,.2f}"
                    amount_paid = f"₦{float(payment.get('amount_paid', 0)) :,.2f}"
                    discount_allowed = f"₦{float(payment.get('discount_allowed', 0)) :,.2f}"
                    balance_due = f"₦{float(payment.get('balance_due', 0)) :,.2f}"

                    self.search_tree.insert("", "end", values=(
                        payment.get("id", ""),
                        payment.get("event_id", ""),
                        payment.get("organiser", ""),
                        event_amount,
                        amount_paid,
                        discount_allowed,
                        balance_due,
                        payment.get("payment_method", ""),
                        payment.get("payment_status", ""),
                        payment.get("payment_date", ""),
                        payment.get("created_by", ""),
                    ))
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

        tk.Label(frame, text="Void Event Payment", font=("Arial", 14, "bold"), bg="#ffffff").pack(pady=10)

        input_frame = tk.Frame(frame, bg="#ffffff")
        input_frame.pack(pady=5)

        tk.Label(input_frame, text="Payment ID:", font=("Arial", 11), bg="#ffffff").grid(row=0, column=0, padx=5, pady=5)
        self.payment_id_entry = tk.Entry(input_frame, font=("Arial", 11))
        self.payment_id_entry.grid(row=0, column=1, padx=5, pady=5)

        void_btn = ttk.Button(input_frame, text="Void Payment", command=self.process_void_event_payment)
        void_btn.grid(row=0, column=2, padx=10, pady=5)

        table_frame = tk.Frame(frame, bg="#ffffff")
        table_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("Payment ID", "Organiser", "Amount Paid", "Discount Allowed", "Balance Due", "Payment Status", "Created By")

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

    def process_void_event_payment(self):
        payment_id = self.payment_id_entry.get().strip()

        if not payment_id.isdigit():
            messagebox.showerror("Error", "Please enter a valid numeric payment ID.")
            return

        try:
            check_url = f"http://127.0.0.1:8000/eventpayment/{payment_id}"
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.get(check_url, headers=headers)

            if response.status_code == 200:
                payment_data = response.json()
                payment_status = payment_data.get("payment_status", "").lower()

                if payment_status == "void":
                    messagebox.showerror("Error", f"Payment ID {payment_id} has already been voided.")
                    return
                
                void_url = f"http://127.0.0.1:8000/eventpayment/{payment_id}/void"
                void_response = requests.put(void_url, headers=headers)

                if void_response.status_code == 200:
                    data = void_response.json()
                    messagebox.showinfo("Success", data.get("message", "Payment voided successfully."))
                    self.fetch_voided_event_payment_by_id(payment_id)
                else:
                    messagebox.showerror("Error", void_response.json().get("detail", "Failed to void payment."))
            else:
                messagebox.showerror("Error", response.json().get("detail", "Payment record not found."))

        except requests.exceptions.RequestException as e:
            messagebox.showerror("Error", f"Request failed: {e}")

    def fetch_voided_event_payment_by_id(self, payment_id=None):
        if payment_id is None:
            payment_id = self.payment_id_entry.get().strip()

        if not payment_id.isdigit():
            messagebox.showerror("Error", "Please enter a valid numeric payment ID.")
            return

        try:
            api_url = f"http://127.0.0.1:8000/eventpayment/{payment_id}"
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.get(api_url, headers=headers)

            if response.status_code == 200:
                data = response.json()

                if data:
                    if hasattr(self, "void_payment_tree") and self.void_payment_tree is not None:
                        self.void_payment_tree.delete(*self.void_payment_tree.get_children())

                    self.void_payment_tree.insert("", "end", values=(
                        data.get("id", ""),
                        data.get("organiser", ""),
                        f"₦{float(data.get('amount_paid', 0)) :,.2f}",
                        f"₦{float(data.get('discount_allowed', 0)) :,.2f}",
                        f"₦{float(data.get('balance_due', 0)) :,.2f}",
                        data.get("payment_status", ""),
                        data.get("created_by", ""),
                    ))
                else:
                    messagebox.showinfo("No Results", "No payment found with the provided ID.")
            else:
                messagebox.showerror("Error", response.json().get("detail", "No payment found."))

        except requests.exceptions.RequestException as e:
            messagebox.showerror("Error", f"Request failed: {e}")

    
    
    
    
    
    
      
    #def create_event(self):
        #pass
    
    #def list_events(self):
        #pass
    
    
    #def search_event_by_id(self):
        #pass
    
    #def update_event(self):
        #pass
    
    #def cancel_event(self):
        #pass
    
    
    
    
    
    #def create_event_payment(self):
        #pass
    
    #def list_events_payment(self):
        #pass
    
    #def list_payment_by_status(self):
        #pass
    
    #def search_Payment_by_id(self):
        #pass
    
    #def void_payment(self):
        #pass



# Main Execution
if __name__ == "__main__":
    root = tk.Tk()
    app = EventManagement(root)
    root.mainloop()    