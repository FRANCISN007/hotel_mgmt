import tkinter as tk
from license_gui import LicenseGUI
from login_gui import LoginGUI
import requests
from tkinter import messagebox
from PIL import Image, ImageTk
import os
import win32print
import win32ui



API_URL = "http://localhost:8000/license"  # FastAPI server URL

class Application:
    def __init__(self, root):
        self.root = root
        self.check_license()

    def check_license(self):
        # Request to verify license - this is done via an API call
        try:
            response = requests.get(f"{API_URL}/verify/YOUR_LICENSE_KEY")
            
            if response.status_code == 200:
                # License is valid, move to login screen
                self.show_login_screen()
            else:
                # License is invalid, show the license input screen
                self.show_license_screen()
        except requests.exceptions.RequestException:
            # Handle case where backend is unreachable or any other network issues
            print("License verification failed or backend is unreachable.")
            self.show_license_screen()

    def show_license_screen(self):
        # License input screen for the user
        self.license_screen = LicenseGUI(self.root, self.show_login_screen)
        self.license_screen.pack()

    def show_login_screen(self):
        if hasattr(self, 'license_screen'):
            self.license_screen.pack_forget()  

        self.login_screen = LoginGUI(self.root)
        self.login_screen.pack()

        # Ensure the print button is created
        self.create_print_button()


    def create_print_button(self):
        try:
            # Define the path to the printer icon
            img_path = os.path.join("frontend", "assets", "printer_icon.png")
            
            if not os.path.exists(img_path):
                messagebox.showerror("Image Error", f"Printer icon not found at: {img_path}")
                return

            # Open, resize, and convert the image
            printer_img = Image.open(img_path)
            printer_img = printer_img.resize((30, 30))  
            self.printer_icon = ImageTk.PhotoImage(printer_img)  # Store reference

            # Create the print button
            self.print_button = tk.Button(self.root, image=self.printer_icon, command=self.print_report)
            self.print_button.pack(pady=20)

        except Exception as e:
            messagebox.showerror("Image Error", f"Could not load printer icon: {e}")

    def print_report(self):
        try:
            # Get the default printer
            printer_name = win32print.GetDefaultPrinter()
            messagebox.showinfo("Print", f"Printing report on: {printer_name}")

            # Printer setup
            hprinter = win32print.OpenPrinter(printer_name)
            pdc = win32ui.CreateDC()
            pdc.CreatePrinterDC(printer_name)
            pdc.StartDoc('Hotel Report')
            pdc.StartPage()

            # Example of text to print (replace with report content)
            pdc.TextOut(100, 100, "Hotel Management System Report")
            pdc.TextOut(100, 150, "Generated Booking Details...")

            pdc.EndPage()
            pdc.EndDoc()
            pdc.DeleteDC()

        except Exception as e:
            messagebox.showerror("Print Error", f"Could not print: {e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = Application(root)
    root.mainloop()
