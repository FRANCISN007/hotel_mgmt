# main.py
import tkinter as tk
from login_gui import LoginGUI

if __name__ == "__main__":
    root = tk.Tk()
    app = LoginGUI(root)
    root.mainloop()
