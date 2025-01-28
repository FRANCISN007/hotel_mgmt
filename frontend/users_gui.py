import tkinter as tk
from tkinter import ttk, messagebox
import requests



class UserManagement:
    def __init__(self, parent, token):
        self.token = token
        self.parent = parent

        # Create a new Toplevel window for user management
        self.user_management_window = tk.Toplevel(parent)
        self.user_management_window.title("User Management")
        self.user_management_window.geometry("800x600")

        self.api_base_url = "http://127.0.0.1:8000"  # Adjusted to match your FastAPI base URL
        
        # Display user management options (Add, Update, Delete)
        self.display_user_management_options()

        # Create Treeview for displaying users
        self.users_treeview = ttk.Treeview(self.user_management_window, columns=("ID", "Username", "Role"), show="headings")
        self.users_treeview.heading("ID", text="ID")
        self.users_treeview.heading("Username", text="Username")
        self.users_treeview.heading("Role", text="Role")
        self.users_treeview.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Load users from API
        self.fetch_users()

    def display_user_management_options(self):
        # Frame for management buttons
        options_frame = ttk.Frame(self.user_management_window)
        options_frame.pack(fill=tk.X, pady=10)

        # Add User Button
        add_button = ttk.Button(options_frame, text="Add User", command=self.add_user)
        add_button.grid(row=0, column=0, padx=10)

        # Update User Button
        update_button = ttk.Button(options_frame, text="Update User", command=self.update_user)
        update_button.grid(row=0, column=1, padx=10)

        # Delete User Button
        delete_button = ttk.Button(options_frame, text="Delete User", command=self.delete_user)
        delete_button.grid(row=0, column=2, padx=10)

    def fetch_users(self, skip=0, limit=10):
        try:
            response = requests.get(
                f"http://127.0.0.1:8000/users/?skip={skip}&limit={limit}",
                headers={"Authorization": f"Bearer {self.token}"}
            )

            if response.status_code == 200:
                users = response.json()
            # Clear and populate the Treeview
                for row in self.users_treeview.get_children():
                    self.users_treeview.delete(row)
                for user in users:
                    self.users_treeview.insert("", tk.END, values=(user["id"], user["username"], user["role"]))

            elif response.status_code == 404:  # Unauthorized
                messagebox.showerror("Unauthorized", "Invalid or expired token. Please log in again.")
            # Redirect to login or close the current window
                self.user_management_window.destroy()
            else:
                messagebox.showerror("Error", f"Failed to retrieve users. Status code: {response.status_code}")

        except requests.RequestException as e:
            messagebox.showerror("Error", f"Error fetching users: {e}")



    def add_user(self):
        # Open a window to input new user details
        self.add_user_window = tk.Toplevel(self.user_management_window)
        self.add_user_window.title("Add User")
        self.add_user_window.geometry("400x300")
        
        # Add user form
        username_label = ttk.Label(self.add_user_window, text="Username:")
        username_label.pack(anchor=tk.W, padx=20)
        self.new_username_entry = ttk.Entry(self.add_user_window, width=30)
        self.new_username_entry.pack(padx=20, pady=5)
        
        password_label = ttk.Label(self.add_user_window, text="Password:")
        password_label.pack(anchor=tk.W, padx=20)
        self.new_password_entry = ttk.Entry(self.add_user_window, width=30, show="*")
        self.new_password_entry.pack(padx=20, pady=5)

        role_label = ttk.Label(self.add_user_window, text="Role:")
        role_label.pack(anchor=tk.W, padx=20)
        self.new_role_entry = ttk.Entry(self.add_user_window, width=30)
        self.new_role_entry.pack(padx=20, pady=5)

        add_button = ttk.Button(self.add_user_window, text="Add", command=self.submit_new_user)
        add_button.pack(pady=20)

    def submit_new_user(self):
        username = self.new_username_entry.get()
        password = self.new_password_entry.get()
        role = self.new_role_entry.get()

        if not username or not password or not role:
            messagebox.showerror("Error", "All fields are required.")
            return

        try:
            data = {"username": username, "password": password, "role": role}
            response = requests.post(
                "http://127.0.0.1:8000/users/register",  # Ensure this is correct
                json=data,
                headers={"Authorization": f"Bearer {self.token}"}
            )

        # Log response for debugging
            print(f"Response Status Code: {response.status_code}")
            print(f"Response Content: {response.text}")

        # Check if the user was added successfully
            if response.status_code == 201 or response.ok:
                messagebox.showinfo("Success", "User added successfully!")
                self.add_user_window.destroy()  # Close the add user window
                self.fetch_users()  # Refresh user list
            else:
                error_message = response.json().get("detail", "Unknown error occurred.")
                messagebox.showerror("Error", f"Failed to add user: {error_message}")
                print(f"Failed to add user. Status code: {response.status_code}, Response: {response.text}")
        except requests.RequestException as e:
            messagebox.showerror("Error", f"Error adding user: {e}")
            print(f"Error adding user: {e}")


    def update_user(self):
        # Get selected user from the Treeview
        selected_item = self.users_treeview.selection()
        if not selected_item:
            messagebox.showerror("Error", "Please select a user to update.")
            return

        user_id = self.users_treeview.item(selected_item)["values"][0]  # Get user ID from selection
        username = self.users_treeview.item(selected_item)["values"][1]  # Get username
        role = self.users_treeview.item(selected_item)["values"][2]  # Get role

        # Open a window to input updated user details
        self.update_user_window = tk.Toplevel(self.user_management_window)
        self.update_user_window.title("Update User")
        self.update_user_window.geometry("400x300")
        
        # Update user form
        username_label = ttk.Label(self.update_user_window, text="Username:")
        username_label.pack(anchor=tk.W, padx=20)
        self.updated_username_entry = ttk.Entry(self.update_user_window, width=30)
        self.updated_username_entry.insert(0, username)
        self.updated_username_entry.pack(padx=20, pady=5)
        
        role_label = ttk.Label(self.update_user_window, text="Role:")
        role_label.pack(anchor=tk.W, padx=20)
        self.updated_role_entry = ttk.Entry(self.update_user_window, width=30)
        self.updated_role_entry.insert(0, role)
        self.updated_role_entry.pack(padx=20, pady=5)

        update_button = ttk.Button(self.update_user_window, text="Update", command=self.submit_updated_user)
        update_button.pack(pady=20)

    def submit_updated_user(self):
        updated_username = self.updated_username_entry.get()
        updated_role = self.updated_role_entry.get()

        if not updated_username or not updated_role:
            messagebox.showerror("Error", "All fields are required.")
            return

        # Send updated data to backend
        data = {"username": updated_username, "role": updated_role}
        selected_item = self.users_treeview.selection()
        username = self.users_treeview.item(selected_item)["values"][1]  # Get username of selected user

        try:
            response = requests.put(
                f"http://127.0.0.1:8000/users/{username}",
                json=data,
                headers={"Authorization": f"Bearer {self.token}"}
            )

            if response.status_code == 200:
                messagebox.showinfo("Success", "User updated successfully!")
                self.update_user_window.destroy()  # Close the update user window
                self.fetch_users()  # Refresh user list
            else:
                messagebox.showerror("Error", "Failed to update user.")
        except requests.RequestException as e:
            messagebox.showerror("Error", f"Error updating user: {e}")

    def delete_user(self):
        # Get selected user from the Treeview
        selected_item = self.users_treeview.selection()
        if not selected_item:
            messagebox.showerror("Error", "Please select a user to delete.")
            return

        user_id = self.users_treeview.item(selected_item)["values"][0]  # Get user ID from selection
        username = self.users_treeview.item(selected_item)["values"][1]  # Get username

        # Confirm deletion
        confirmation = messagebox.askyesno("Delete User", f"Are you sure you want to delete user {username}?")
        if confirmation:
            try:
                # Send delete request to backend
                response = requests.delete(
                    f"http://127.0.0.1:8000/users/{username}",
                    headers={"Authorization": f"Bearer {self.token}"}
                )

                if response.status_code == 200:
                    messagebox.showinfo("Success", f"User {username} deleted successfully!")
                    self.fetch_users()  # Refresh user list
                else:
                    messagebox.showerror("Error", f"Failed to delete user {username}.")
            except requests.RequestException as e:
                messagebox.showerror("Error", f"Error deleting user: {e}")
