import tkinter as tk
from tkinter import ttk, messagebox
import requests
from utils import BASE_URL
from tkcalendar import DateEntry


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
        separator = tk.Frame(self.left_frame, height=4, bg="#333333")
        separator.pack(fill="x", padx=5, pady=10)
        
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
   
        
        
        
        
        
        
        
        
        
        
        
        
        
        
    
    #def create_event(self):
        #pass
    
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
