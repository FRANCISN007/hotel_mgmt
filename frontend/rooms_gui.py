import tkinter as tk
from tkinter import ttk, messagebox
from utils import api_request, get_user_role
import re

class RoomManagement:
    def __init__(self, root, token):
        self.root = tk.Toplevel(root)
        self.token = token
        self.root.title("Room Management")

        # Set window size and position at the center
        window_width = 800
        window_height = 600
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x_coordinate = (screen_width // 2) - (window_width // 2)
        y_coordinate = (screen_height // 2) - (window_height // 2)
        self.root.geometry(f"{window_width}x{window_height}+{x_coordinate}+{y_coordinate}")

        self.user_role = get_user_role(self.token)

        self.setup_ui()
        self.fetch_rooms()

        style = ttk.Style()
        style.configure("Treeview.Heading", font=("Helvetica", 12, "bold"))
        style.configure("Treeview", font=("Helvetica", 11))  # Increase row font size

    def natural_sort_key(self, room):
        """Sort room numbers correctly, handling both numeric and alphanumeric values."""
        room_number = str(room.get("room_number", ""))  # Ensure it's a string
        parts = re.split(r'(\d+)', room_number)  # Split letters and numbers
        return [int(part) if part.isdigit() else part for part in parts]  # Convert numeric parts to int

    def setup_ui(self):
        self.root.configure(bg="#f0f0f0")  # Set the background color of the main window

        title_label = tk.Label(self.root, text="Room Management", font=("Helvetica", 18, "bold"),
                               bg="#007BFF", fg="white", padx=10, pady=10)
        title_label.pack(fill=tk.X)

        columns = ("Room Number", "Room Type", "Amount", "Status", "Booking Type")
        self.tree = ttk.Treeview(self.root, columns=columns, show="headings")

        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=140, anchor="center")
        self.tree.pack(pady=10, fill=tk.BOTH, expand=True)

        btn_frame = tk.Frame(self.root, bg="#f0f0f0")  # Set background color for button frame
        btn_frame.pack(pady=10)

        self.add_button = ttk.Button(btn_frame, text="➕ Add Room", command=self.open_room_form)
        self.add_button.pack(side=tk.LEFT, padx=5, pady=5, ipadx=10)

        self.update_button = ttk.Button(btn_frame, text="✏️ Update Room", command=self.update_room)
        self.update_button.pack(side=tk.LEFT, padx=5, pady=5, ipadx=10)

        self.delete_button = ttk.Button(btn_frame, text="❌ Delete Room", command=self.delete_room)
        self.delete_button.pack(side=tk.LEFT, padx=5, pady=5, ipadx=10)

        self.available_rooms_button = ttk.Button(btn_frame, text="🟢 List Available Rooms", command=self.list_available_rooms)
        self.available_rooms_button.pack(side=tk.LEFT, padx=5, pady=5, ipadx=10)

        self.refresh_button = ttk.Button(btn_frame, text="🔄 Refresh", command=self.fetch_rooms)
        self.refresh_button.pack(side=tk.LEFT, padx=5, pady=5, ipadx=10)

        

        if self.user_role != "admin":
            self.delete_button.config(state=tk.DISABLED)
            self.update_button.config(state=tk.DISABLED)
            self.add_button.config(state=tk.DISABLED)



   

    def fetch_rooms(self):
        """Fetch all rooms from the API and update the display with their latest statuses, sorted naturally."""
        response = api_request("/rooms", "GET", token=self.token)

        if not response or "rooms" not in response:
            messagebox.showerror("Error", "Failed to fetch rooms")
            return

        self.tree.delete(*self.tree.get_children())  # Clear existing entries

        rooms = response["rooms"]  # Get the list of rooms

        # Sort rooms using natural sorting (handles "A1", "B2", "101" correctly)
        rooms.sort(key=self.natural_sort_key)  # Use self.natural_sort_key()

        for room in rooms:
            room_number = room.get("room_number", "N/A")
            room_type = room.get("room_type", "N/A")
            amount = room.get("amount", "N/A")

            # Fetch the latest status for each room
            room_details = api_request(f"/rooms/{room_number}", "GET", token=self.token)
            current_status = room_details.get("status", "N/A") if room_details else room.get("status", "N/A")
            booking_type = room_details.get("booking_type", "N/A") if room_details else "No active booking"

            # Insert the room details into the display
            self.tree.insert("", tk.END, values=(room_number, room_type, amount, current_status, booking_type))
            
            
            
            
            
            

    def list_available_rooms(self):
        """Fetch and display available rooms."""
        response = api_request("/rooms/available", "GET", token=self.token)

        if not response or "available_rooms" not in response:
            messagebox.showerror("Error", "Failed to fetch available rooms")
            return

        available_rooms = response["available_rooms"]
        
        # Sort available rooms using natural sorting
        available_rooms.sort(key=self.natural_sort_key)  # Use self.natural_sort_key()


        available_window = tk.Toplevel(self.root)
        available_window.title("Available Rooms")
        available_window.geometry("500x300")

        ttk.Label(available_window, text="Available Rooms", font=("Helvetica", 14, "bold")).pack(pady=10)

        tree = ttk.Treeview(available_window, columns=("Room Number", "Room Type", "Amount"), show="headings")
        for col in ("Room Number", "Room Type", "Amount"):
            tree.heading(col, text=col)
            tree.column(col, width=150, anchor="center")
        tree.pack(pady=10, fill=tk.BOTH, expand=True)

        for room in available_rooms:
            
            tree.insert("", tk.END, values=(room["room_number"], room["room_type"], room["amount"]))

        ttk.Button(available_window, text="Close", command=available_window.destroy).pack(pady=10)



    def open_room_form(self):
        form = tk.Toplevel(self.root)
        form.title("Add Room")
        form.geometry("300x300")

        tk.Label(form, text="Room Number:").pack()
        room_number_entry = tk.Entry(form)
        room_number_entry.pack()

        tk.Label(form, text="Room Type:").pack()
        room_type_entry = tk.Entry(form)
        room_type_entry.pack()

        tk.Label(form, text="Amount:").pack()
        amount_entry = tk.Entry(form)
        amount_entry.pack()

        tk.Label(form, text="Status:").pack()
        status_options = ["available", "checked-in", "reserved"]
        status_entry = ttk.Combobox(form, values=status_options, state="readonly")
        status_entry.pack()
        status_entry.current(0)

        def submit():
            room_number = room_number_entry.get()
            response = api_request("/rooms", "GET", token=self.token)
            if response and "rooms" in response:
                if any(room["room_number"] == room_number for room in response["rooms"]):
                    messagebox.showerror("Error", f"Room {room_number} already exists!")
                    return

            data = {
                "room_number": room_number,
                "room_type": room_type_entry.get(),
                "amount": amount_entry.get(),
                "status": status_entry.get()
            }

            add_response = api_request("/rooms", "POST", data, self.token)
            if add_response:
                messagebox.showinfo("Success", "Room added successfully")
                form.destroy()
                self.fetch_rooms()
            else:
                messagebox.showerror("Error", "Failed to add room")

        submit_button = tk.Button(form, text="Submit", command=submit)
        submit_button.pack(pady=10)

    def update_room(self):
        """Update selected room details."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a room to update")
            return

    # Get selected room details
        values = self.tree.item(selected[0], "values")
        room_number = values[0]  # Current room number
        
        

    # Fetch the full room details from API
        # Fetch the full room details from API
        response = api_request(f"/rooms/{room_number}", "GET", token=self.token)

# # Debugging: Print response to see what is returned
        print("API Response:", response)

# Ensure the response contains valid data
        if not response or not isinstance(response, dict) or "room_number" not in response:
            messagebox.showerror("Error", f"Failed to fetch room details. Response: {response}")
            return

        room_data = response  # Assign the response directly if valid

    # Prevent updates if the room is checked-in
        if room_data["status"] == "checked-in":
            messagebox.showwarning("Warning", "Room cannot be updated as it is currently checked-in")
            return

    # Create update window
        update_window = tk.Toplevel(self.root)
        update_window.title("Update Room")
        update_window.geometry("300x300")

    # Room Number
        tk.Label(update_window, text="Room Number:").pack()
        room_number_entry = tk.Entry(update_window)
        room_number_entry.insert(0, room_data["room_number"])
        room_number_entry.pack()

    # Room Type
        tk.Label(update_window, text="Room Type:").pack()
        room_type_entry = tk.Entry(update_window)
        room_type_entry.insert(0, room_data["room_type"])
        room_type_entry.pack()

    # Amount
        tk.Label(update_window, text="Amount:").pack()
        amount_entry = tk.Entry(update_window)
        amount_entry.insert(0, str(room_data["amount"]))
        amount_entry.pack()

    # Status Dropdown
        tk.Label(update_window, text="Select New Status:").pack()
        status_options = ["available", "checked-in", "reserved"]
        status_entry = ttk.Combobox(update_window, values=status_options, state="readonly")
        status_entry.pack()
        status_entry.set(room_data["status"])  # Set current status as default

        def submit_update():
            """Submit updated room data to API."""
            new_room_number = room_number_entry.get()
            new_room_type = room_type_entry.get()
            new_amount = amount_entry.get()
            new_status = status_entry.get()

        # Validate input
            if not new_room_number or not new_room_type or not new_amount:
                messagebox.showwarning("Warning", "All fields must be filled")
                return

        # Convert amount to float
            try:
                new_amount = float(new_amount)
            except ValueError:
                messagebox.showwarning("Warning", "Amount must be a number")
                return

        # Prepare update payload
            data = {
                "room_number": new_room_number,
                "room_type": new_room_type,
             "amount": new_amount,
                "status": new_status
            }

        # Send update request
            response = api_request(f"/rooms/{room_number}", "PUT", data, self.token)
            if response:
                messagebox.showinfo("Success", "Room updated successfully")
                update_window.destroy()
                self.fetch_rooms()
            else:
                messagebox.showerror("Error", "Failed to update room")

    # Submit Button
        submit_button = tk.Button(update_window, text="Update", command=submit_update)
        submit_button.pack(pady=10)


    def delete_room(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a room to delete")
            return

        room_number = self.tree.item(selected[0], "values")[0]
        confirm = messagebox.askyesno("Confirm", f"Are you sure you want to delete room {room_number}?")
        if confirm:
            response = api_request(f"/rooms/{room_number}", "DELETE", token=self.token)
            if response:
                messagebox.showinfo("Success", "Room deleted successfully")
                self.fetch_rooms()
            else:
                messagebox.showerror("Error", "Failed to delete room")

if __name__ == "__main__":
    root = tk.Tk()
    RoomManagement(root, "your_token_here")
    root.mainloop()