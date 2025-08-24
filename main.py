import tkinter as tk
from gui import ShopApp

def main():
    root = tk.Tk()
    app = ShopApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()