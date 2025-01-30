import tkinter as tk
from tkinter import ttk, messagebox
from utils import api_request, get_user_role

class RoomManagement:
    def __init__(self, root, token):
        self.root = root
        self.token = token
        self.root.title("Room Management")
        self.root.geometry("900x600")
        self.root.configure(bg="#f4f4f4")  # Light gray background
        self.user_role = get_user_role(self.token)

        self.setup_ui()
        self.fetch_rooms()
    
    def setup_ui(self):
        # Title Bar
        title_frame = tk.Frame(self.root, bg="#003366", height=60)
        title_frame.pack(fill=tk.X)
        title_label = tk.Label(
            title_frame, text="Room Management", font=("Helvetica", 18, "bold"), fg="white", bg="#003366"
        )
        title_label.pack(pady=15)

        # Table Frame
        table_frame = tk.Frame(self.root, bg="#f4f4f4")
        table_frame.pack(pady=20, padx=20, fill=tk.BOTH, expand=True)

        self.tree = ttk.Treeview(
            table_frame, columns=("Room Number", "Type", "Amount", "Status"), show="headings", height=15
        )
        
        # Define column headings
        columns = [("Room Number", 120), ("Type", 150), ("Amount", 120), ("Status", 150)]
        for col, width in columns:
            self.tree.heading(col, text=col, anchor="center")
            self.tree.column(col, width=width, anchor="center")

        self.tree.pack(fill=tk.BOTH, expand=True)

        # Scrollbars
        scrollbar_y = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscroll=scrollbar_y.set)

        # Button Frame
        btn_frame = tk.Frame(self.root, bg="#f4f4f4")
        btn_frame.pack(pady=10)

        self.add_button = ttk.Button(btn_frame, text="Add Room", command=self.open_room_form)
        self.add_button.grid(row=0, column=0, padx=5, pady=5, ipadx=10)
        
        self.update_button = ttk.Button(btn_frame, text="Update Room", command=self.update_room)
        self.update_button.grid(row=0, column=1, padx=5, pady=5, ipadx=10)
        
        self.delete_button = ttk.Button(btn_frame, text="Delete Room", command=self.delete_room)
        self.delete_button.grid(row=0, column=2, padx=5, pady=5, ipadx=10)

        self.refresh_button = ttk.Button(btn_frame, text="Refresh", command=self.fetch_rooms)
        self.refresh_button.grid(row=0, column=3, padx=5, pady=5, ipadx=10)

        # Disable buttons if user is not an admin
        if self.user_role != "admin":
            self.add_button.config(state=tk.DISABLED)
            self.update_button.config(state=tk.DISABLED)
            self.delete_button.config(state=tk.DISABLED)

    def fetch_rooms(self):
        """Fetch rooms from API and populate the treeview."""
        response = api_request("/rooms", "GET")
        if response and isinstance(response, dict) and "rooms" in response:  # Fix: Checking nested 'rooms' key
            self.tree.delete(*self.tree.get_children())  # Clear old data
            for room in response["rooms"]:  # Fix: Fetching from 'rooms' key
                self.tree.insert("", tk.END, values=(
                    room.get("room_number", "N/A"), 
                    room.get("room_type", "N/A"), 
                    room.get("amount", "N/A"), 
                    room.get("status", "N/A")
                ))
        else:
            messagebox.showerror("Error", "Failed to fetch rooms or no data found.")

    def open_room_form(self):
        """Form to add a new room."""
        form = tk.Toplevel(self.root)
        form.title("Add Room")
        form.geometry("350x300")
        form.configure(bg="white")

        tk.Label(form, text="Room Number:", font=("Arial", 12), bg="white").pack(pady=5)
        room_number_entry = tk.Entry(form, font=("Arial", 12))
        room_number_entry.pack(pady=5)

        tk.Label(form, text="Room Type:", font=("Arial", 12), bg="white").pack(pady=5)
        room_type_entry = tk.Entry(form, font=("Arial", 12))
        room_type_entry.pack(pady=5)

        tk.Label(form, text="Amount:", font=("Arial", 12), bg="white").pack(pady=5)
        amount_entry = tk.Entry(form, font=("Arial", 12))
        amount_entry.pack(pady=5)

        def submit():
            data = {
                "room_number": room_number_entry.get(),
                "room_type": room_type_entry.get(),
                "amount": amount_entry.get()
            }
            response = api_request("POST", "/rooms/", data)
            if response:
                messagebox.showinfo("Success", "Room added successfully")
                form.destroy()
                self.fetch_rooms()
            else:
                messagebox.showerror("Error", "Failed to add room")

        submit_button = tk.Button(form, text="Submit", command=submit, bg="#003366", fg="white", font=("Arial", 12))
        submit_button.pack(pady=15)

    def update_room(self):
        """Update room status."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a room to update")
            return

        room_number = self.tree.item(selected[0], "values")[0]
        new_status = messagebox.askstring("Update Room", "Enter new status (available/booked/maintenance/reserved):")
        if new_status:
            response = api_request("PUT", f"/rooms/{room_number}", {"status": new_status})
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
        if messagebox.askyesno("Confirm", f"Are you sure you want to delete room {room_number}?"):
            response = api_request("DELETE", f"/rooms/{room_number}")
            if response:
                messagebox.showinfo("Success", "Room deleted successfully")
                self.fetch_rooms()
            else:
                messagebox.showerror("Error", "Failed to delete room")


if __name__ == "__main__":
    root = tk.Tk()
    RoomManagement(root, "your_token_here")
    root.mainloop()
