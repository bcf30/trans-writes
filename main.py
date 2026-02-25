"""
main.py - entry point for trans-writes

run with: python main.py
"""

import sys
import tkinter as tk
from tkinter import messagebox

from gui import TransWritesApp


def check_dependencies() -> bool:
    """check that required deps are installed, return True if all good"""
    missing = []
    
    try:
        from PIL import Image
    except ImportError:
        missing.append("Pillow")
    
    try:
        import numpy
    except ImportError:
        missing.append("numpy")
    
    if missing:
        print("Missing required dependencies:")
        for dep in missing:
            print(f"  - {dep}")
        print("\nInstall with: pip install " + " ".join(missing))
        return False
    
    return True


def main() -> None:
    """main entry point - creates window and runs the app"""
    if not check_dependencies():
        sys.exit(1)
    
    root = tk.Tk()
    
    # icon setting placeholder for future implementation
    # root.iconbitmap('icon.ico')
    
    try:
        app = TransWritesApp(root)
        root.mainloop()
    except Exception as e:
        messagebox.showerror(
            "Error",
            f"An unexpected error occurred:\n{str(e)}"
        )
        sys.exit(1)


if __name__ == '__main__':
    main()
