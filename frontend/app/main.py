import tkinter as tk
from gui import setup_gui
from desktop_activity import ActivityMonitor

def main():
    root = tk.Tk()
    root.title("Gaze Predictor App")
    root.geometry("800x600")

    activity_monitor = ActivityMonitor()
    setup_gui(root, activity_monitor)

    root.mainloop()

if __name__ == "__main__":
    main()
