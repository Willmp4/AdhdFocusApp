import tkinter as tk
from gui import setup_gui
from desktop_activity import ActivityMonitor
from tkinter import messagebox

def on_closing(activity_monitor, root):
    if messagebox.askokcancel("Quit", "Do you want to quit?"):
        activity_monitor.stop_monitoring()
        root.destroy()

def main():

    root = tk.Tk()
    root.title("Focus Monitoring App")

    # Create an instance of ActivityMonitor
    activity_monitor = ActivityMonitor()

    # Setup the GUI with the activity_monitor instance
    setup_gui(root, activity_monitor)

    # Set the protocol for closing the window
    root.protocol("WM_DELETE_WINDOW", lambda: on_closing(activity_monitor, root))

    # Start the main event loop
    root.mainloop()
if __name__ == "__main__":
    main()
