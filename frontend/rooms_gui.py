import tkinter as tk
from tkinter import ttk, messagebox
from utils import api_request, get_user_role
from tkinter import ttk, messagebox, simpledialog


class RoomManagement:
    def __init__(self, root, token):
        self.root = tk.Toplevel(root)
        self.token = token
        self.root.title("Room Management")
        self.root.geometry("800x500")
        self.user_role = get_user_role(self.token)

        self.setup_ui()
        self.fetch_rooms()  # Fetch rooms at startup

    def setup_ui(self):
        # Header Label with Blue Background
        title_label = tk.Label(self.root, text="Room Management", font=("Helvetica", 18, "bold"),
                               bg="#007BFF", fg="white", padx=10, pady=10)
        title_label.pack(fill=tk.X)

        # Treeview for displaying rooms
        self.tree = ttk.Treeview(self.root, columns=("Room Number", "Type", "Amount", "Status"), show="headings")
        for col in ("Room Number", "Type", "Amount", "Status"):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=140, anchor="center")
        self.tree.pack(pady=10, fill=tk.BOTH, expand=True)

        # Buttons frame
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=10)

        # Buttons
        self.add_button = ttk.Button(btn_frame, text="Add Room", command=self.open_room_form)
        self.add_button.pack(side=tk.LEFT, padx=5, pady=5, ipadx=10)

        self.update_button = ttk.Button(btn_frame, text="Update Room", command=self.update_room)
        self.update_button.pack(side=tk.LEFT, padx=5, pady=5, ipadx=10)

        self.delete_button = ttk.Button(btn_frame, text="Delete Room", command=self.delete_room)
        self.delete_button.pack(side=tk.LEFT, padx=5, pady=5, ipadx=10)

        self.refresh_button = ttk.Button(btn_frame, text="Refresh", command=self.fetch_rooms)
        self.refresh_button.pack(side=tk.LEFT, padx=5, pady=5, ipadx=10)

        # Disable buttons if user is not an admin
        if self.user_role != "admin":
            self.add_button.config(state=tk.DISABLED)
            self.update_button.config(state=tk.DISABLED)
            self.delete_button.config(state=tk.DISABLED)

    def fetch_rooms(self):
        """Fetch all rooms from API and display them."""
        response = api_request("/rooms", "GET", token=self.token)

        if not response:
            messagebox.showerror("Error", "Failed to fetch rooms")
            return

        # Clear the TreeView before inserting new data
        self.tree.delete(*self.tree.get_children())

        # Check if response contains a 'rooms' key
        if "rooms" in response:
            rooms = response["rooms"]
        else:
            rooms = response  # Assume response is already a list

        # Insert room data into the TreeView
        for room in rooms:
            self.tree.insert("", tk.END, values=(
                room.get("room_number", "N/A"),
                room.get("room_type", "N/A"),
                room.get("amount", "N/A"),
                room.get("status", "N/A")
            ))

    def open_room_form(self):
        """Open form to add a new room."""
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

        def submit():
            """Submit room data to API."""
            data = {
                "room_number": room_number_entry.get(),
                "room_type": room_type_entry.get(),
                "amount": amount_entry.get()
            }
            response = api_request("/rooms", "POST", data, self.token)
            if response:
                messagebox.showinfo("Success", "Room added successfully")
                form.destroy()
                self.fetch_rooms()
            else:
                messagebox.showerror("Error", "Failed to add room")

        submit_button = tk.Button(form, text="Submit", command=submit)
        submit_button.pack(pady=10)

    def update_room(self):
        """Update selected room status."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a room to update")
            return

        room_number = self.tree.item(selected[0], "values")[0]
        new_status = simpledialog.askstring("Update Room", "Enter new status (available/booked/maintenance):")

        if new_status:
            response = api_request(f"/rooms/{room_number}", "PUT", {"status": new_status}, self.token)
            if response:
                messagebox.showinfo("Success", "Room updated successfully")
                self.fetch_rooms()
            else:
                messagebox.showerror("Error", "Failed to update room")

    def delete_room(self):
        """Delete a selected room."""
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

# Test the GUI
if __name__ == "__main__":
    root = tk.Tk()
    RoomManagement(root, "your_token_here")
    root.mainloop()
