import sys
import tkinter as tk
from tkinter import messagebox


def check_dependencies() -> bool:
    """Return whether the packages needed to start the app are installed."""
    missing_packages = []
    
    try:
        import PIL
    except ImportError:
        missing_packages.append("Pillow")

    try:
        import numpy
    except ImportError:
        missing_packages.append("numpy")

    if missing_packages:
        print("Missing required dependencies:")
        for package_name in missing_packages:
            print(f"  - {package_name}")
        print("\nInstall with: pip install " + " ".join(missing_packages))
        return False
    
    return True


def main() -> None:
    """Create the window and run the app."""
    if not check_dependencies():
        sys.exit(1)

    from gui import TransWritesApp

    root = tk.Tk()

    try:
        application = TransWritesApp(root)
        root.mainloop()
    except Exception as error:
        messagebox.showerror(
            "Error",
            f"An unexpected error occurred:\n{str(error)}"
        )
        sys.exit(1)


if __name__ == '__main__':
    main()
