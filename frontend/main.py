# main.py
#import tkinter as tk
#from login_gui import LoginGUI

#if __name__ == "__main__":
    #root = tk.Tk()
    #app = LoginGUI(root)
    #root.mainloop()

import tkinter as tk
from license_gui import LicenseGUI
from login_gui import LoginGUI
import requests

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
        # Login screen shown after license verification
        if hasattr(self, 'license_screen'):
            self.license_screen.pack_forget()  # Hide the license screen
        self.login_screen = LoginGUI(self.root)
        self.login_screen.pack()

if __name__ == "__main__":
    root = tk.Tk()
    app = Application(root)
    root.mainloop()
