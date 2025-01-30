import tkinter as tk
from tkinter import ttk, messagebox
from utils import api_request, get_user_role

class RoomManagement:
    def __init__(self, root, token):
        self.root = root
        self.token = token
        self.root.title("Room Management")
        self.root.geometry("800x600")
        self.user_role = get_user_role(self.token)

        self.setup_ui()
        self.fetch_rooms()
    
    def setup_ui(self):
        title_label = ttk.Label(self.root, text="Room Management", font=("Helvetica", 18))
        title_label.pack(pady=20)

        self.tree = ttk.Treeview(self.root, columns=("Room Number", "Type", "Amount", "Status"), show="headings")
        for col in ("Room Number", "Type", "Amount", "Status"):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150)
        self.tree.pack(pady=10, fill=tk.BOTH, expand=True)

        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(pady=10)

        self.add_button = ttk.Button(btn_frame, text="Add Room", command=self.open_room_form)
        self.add_button.pack(side=tk.LEFT, padx=5)
        
        self.update_button = ttk.Button(btn_frame, text="Update Room", command=self.update_room)
        self.update_button.pack(side=tk.LEFT, padx=5)
        
        self.delete_button = ttk.Button(btn_frame, text="Delete Room", command=self.delete_room)
        self.delete_button.pack(side=tk.LEFT, padx=5)

        self.refresh_button = ttk.Button(btn_frame, text="Refresh", command=self.fetch_rooms)
        self.refresh_button.pack(side=tk.LEFT, padx=5)

        if self.user_role != "admin":
            self.add_button.config(state=tk.DISABLED)
            self.update_button.config(state=tk.DISABLED)
            self.delete_button.config(state=tk.DISABLED)

    def fetch_rooms(self):
        response = api_request("/rooms", "GET")
        if response and "rooms" in response:
            self.tree.delete(*self.tree.get_children())
            for room in response["rooms"]:
                self.tree.insert("", tk.END, values=(room["room_number"], room["room_type"], room["amount"], room.get("status", "N/A")))
        else:
            messagebox.showerror("Error", "Failed to fetch rooms")

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
        
        def submit():
            data = {
                "room_number": room_number_entry.get(),
                "room_type": room_type_entry.get(),
                "amount": amount_entry.get()
            }
            response = api_request("POST", "rooms/", data)
            if response:
                messagebox.showinfo("Success", "Room added successfully")
                form.destroy()
                self.fetch_rooms()
            else:
                messagebox.showerror("Error", "Failed to add room")
        
        submit_button = tk.Button(form, text="Submit", command=submit)
        submit_button.pack(pady=10)
    
    def update_room(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a room to update")
            return
        room_number = self.tree.item(selected[0], "values")[0]
        new_status = messagebox.askstring("Update Room", "Enter new status (available/booked/maintenance/reserved):")
        if new_status:
            response = api_request("PUT", f"rooms/{room_number}", {"status": new_status})
            if response:
                messagebox.showinfo("Success", "Room updated successfully")
                self.fetch_rooms()
            else:
                messagebox.showerror("Error", "Failed to update room")
    
    def delete_room(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a room to delete")
            return
        room_number = self.tree.item(selected[0], "values")[0]
        if messagebox.askyesno("Confirm", f"Are you sure you want to delete room {room_number}?"):
            response = api_request("DELETE", f"rooms/{room_number}")
            if response:
                messagebox.showinfo("Success", "Room deleted successfully")
                self.fetch_rooms()
            else:
                messagebox.showerror("Error", "Failed to delete room")

if __name__ == "__main__":
    root = tk.Tk()
    RoomManagement(root, "your_token_here")
    root.mainloop()
