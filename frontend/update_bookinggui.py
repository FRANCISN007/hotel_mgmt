import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
import requests
#from bookings_gui import UpdateBooking


class UpdateBooking:
    def __init__(self, root, token):
        self.root = tk.Toplevel(root)
        self.root.title("Update Booking")
        self.root.geometry("900x600")
        self.token = token
        self.root.configure(bg="#f0f0f0")
        
        
    def update_booking(self):
        style = ttk.Style()
        style.configure("Treeview.Heading", font=("Helvetica", 12, "bold"))
        style.configure("Treeview", font=("Helvetica", 11))

        # Header Section
        self.header_frame = tk.Frame(self.root, bg="#A0A0A0", height=50)
        self.header_frame.pack(fill=tk.X)

        self.header_label = tk.Label(self.header_frame, text="Update Booking", fg="white", bg="#A0A0A0", font=("Helvetica", 16, "bold"))
        self.header_label.pack(pady=10)

        # Create frame for booking form
        self.form_frame = tk.Frame(self.root, bg="#ffffff", padx=20, pady=20)
        self.form_frame.pack(fill=tk.BOTH, expand=True)

        # Booking ID
        tk.Label(self.form_frame, text="Booking ID:", font=("Arial", 11), bg="#ffffff").grid(row=0, column=0, padx=5, pady=5)
        self.booking_id_entry = tk.Entry(self.form_frame, font=("Arial", 11))
        self.booking_id_entry.grid(row=0, column=1, padx=5, pady=5)

        # Room Number
        tk.Label(self.form_frame, text="Room Number:", font=("Arial", 11), bg="#ffffff").grid(row=1, column=0, padx=5, pady=5)
        self.room_number_entry = tk.Entry(self.form_frame, font=("Arial", 11))
        self.room_number_entry.grid(row=1, column=1, padx=5, pady=5)

        # Guest Name
        tk.Label(self.form_frame, text="Guest Name:", font=("Arial", 11), bg="#ffffff").grid(row=2, column=0, padx=5, pady=5)
        self.guest_name_entry = tk.Entry(self.form_frame, font=("Arial", 11))
        self.guest_name_entry.grid(row=2, column=1, padx=5, pady=5)

        # Start Date
        tk.Label(self.form_frame, text="Arrival Date:", font=("Arial", 11), bg="#ffffff").grid(row=3, column=0, padx=5, pady=5)
        self.start_date_entry = DateEntry(self.form_frame, font=("Arial", 11), width=12, background="darkblue", foreground="white", borderwidth=2)
        self.start_date_entry.grid(row=3, column=1, padx=5, pady=5)

        # End Date
        tk.Label(self.form_frame, text="Departure Date:", font=("Arial", 11), bg="#ffffff").grid(row=4, column=0, padx=5, pady=5)
        self.end_date_entry = DateEntry(self.form_frame, font=("Arial", 11), width=12, background="darkblue", foreground="white", borderwidth=2)
        self.end_date_entry.grid(row=4, column=1, padx=5, pady=5)

        # Status
        tk.Label(self.form_frame, text="Status:", font=("Arial", 11), bg="#ffffff").grid(row=5, column=0, padx=5, pady=5)
        self.status_combobox = ttk.Combobox(self.form_frame, font=("Arial", 11), values=["confirmed", "checked-in", "checked-out", "cancelled"], state="readonly")
        self.status_combobox.grid(row=5, column=1, padx=5, pady=5)

        # Update Button
        self.update_btn = ttk.Button(self.form_frame, text="Update Booking", command=self.update_booking)
        self.update_btn.grid(row=6, column=0, columnspan=2, pady=15)

    def update_booking(self):
        booking_id = self.booking_id_entry.get().strip()
        room_number = self.room_number_entry.get().strip()
        guest_name = self.guest_name_entry.get().strip()
        arrival_date = self.start_date_entry.get_date().strftime("%Y-%m-%d")
        departure_date = self.end_date_entry.get_date().strftime("%Y-%m-%d")
        status = self.status_combobox.get()

        # Validate inputs
        if not booking_id or not room_number or not guest_name or not status:
            messagebox.showerror("Error", "Please fill all fields.")
            return

        try:
            # Prepare data for API request
            api_url = f"http://127.0.0.1:8000/update/"
            headers = {"Authorization": f"Bearer {self.token}"}
            data = {
                "booking_id": int(booking_id),
                "updated_data": {
                    "room_number": room_number,
                    "guest_name": guest_name,
                    "arrival_date": arrival_date,
                    "departure_date": departure_date,
                    "status": status
                }
            }

            response = requests.put(api_url, json=data, headers=headers)

            if response.status_code == 200:
                # Successfully updated booking
                messagebox.showinfo("Success", "Booking updated successfully.")
            else:
                # Error updating booking
                messagebox.showerror("Error", response.json().get("detail", "Failed to update booking."))

        except requests.exceptions.RequestException as e:
            messagebox.showerror("Error", f"Request failed: {e}")
