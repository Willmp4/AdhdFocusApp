import tkinter as tk
from tkinter import messagebox
from api import register_user, login_user, predict_gaze

def setup_gui(root, activity_monitor):
    login_frame = tk.Frame(root)
    login_frame.pack()

    username_entry = tk.Entry(login_frame)
    username_entry.pack()
    password_entry = tk.Entry(login_frame, show="*")
    password_entry.pack()

    register_button = tk.Button(login_frame, text="Register", command=lambda: register_user(username_entry.get(), password_entry.get()))
    register_button.pack()
    login_button = tk.Button(login_frame, text="Login", command=lambda: login_user(username_entry.get(), password_entry.get()))
    login_button.pack()

    start_monitor_button = tk.Button(login_frame, text="Start Monitoring", command=activity_monitor.start_monitoring)
    start_monitor_button.pack()
