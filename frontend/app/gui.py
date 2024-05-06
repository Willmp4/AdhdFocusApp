import tkinter as tk
from tkinter import messagebox
import pyautogui as pag
from api import register_user, login_user, has_been_calibrated, mark_as_calibrated
from frontend.app.calibration_component import CalibrationComponent
from sklearn.ensemble import RandomForestRegressor
from sklearn.externals import joblib
import numpy as np
import pickle
import os

def load_data(calibration_file):
    # Load calibration data from a pickle file
    with open(calibration_file, 'rb') as f:
        data = pickle.load(f)
    features = np.array(data['images'])
    labels = np.array(data['gaze_coords'])
    return features, labels

def update_model(username, model_path='eye_gaze_model.pkl'):
    calibration_file = f'calibration_data_{username}.pkl'  # File path for user-specific calibration data
    if not os.path.exists(calibration_file):
        print("Calibration file does not exist.")
        return

    model = joblib.load(model_path) if os.path.exists(model_path) else RandomForestRegressor(n_estimators=100)
    features, labels = load_data(calibration_file)
    model.fit(features, labels)
    joblib.dump(model, model_path)
    print("Model updated and saved.")

class LoginFrame(tk.Frame):
    def __init__(self, parent, controller, activity_monitor):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.activity_monitor = activity_monitor

        username_label = tk.Label(self, text="Username:")
        username_label.pack()
        self.username_entry = tk.Entry(self)
        self.username_entry.pack()

        password_label = tk.Label(self, text="Password:")
        password_label.pack()
        password_entry = tk.Entry(self, show="*")
        password_entry.pack()

        register_button = tk.Button(self, text="Register", command=lambda: register_user(self.username_entry.get(), password_entry.get()))
        register_button.pack()
        login_button = tk.Button(self, text="Login", command=lambda: self.attempt_login(self.username_entry.get(), password_entry.get()))
        login_button.pack()

    def attempt_login(self, username, password):
        if login_user(username, password):
            if not has_been_calibrated(username):
                # Launch calibration process
                self.launch_calibration(username)
            else:
                show_frame(MonitoringFrame, self.controller)
        else:
            messagebox.showerror("Login failed", "The username or password is incorrect or an error occurred.")

    def launch_calibration(self, username):
        root = tk.Toplevel()
        root.title("Calibration Component")
        root.geometry(f"{pag.size()[0]}x{pag.size()[1]}")
        app = CalibrationComponent(root, lambda: self.complete_calibration(username))
        root.mainloop()

    def complete_calibration(self, username):
        mark_as_calibrated(username)
        update_model(username)  # Update the model with the new calibration data
        show_frame(MonitoringFrame, self.controller)

class MonitoringFrame(tk.Frame):
    def __init__(self, parent, controller, activity_monitor):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.activity_monitor = activity_monitor

        start_monitor_button = tk.Button(self, text="Start Monitoring", command=self.activity_monitor.start_monitoring)
        start_monitor_button.pack()

        logout_button = tk.Button(self, text="Logout", command=lambda: show_frame(LoginFrame, controller))
        logout_button.pack()


def setup_gui(root, activity_monitor):
    # Create a dictionary to hold references to different frames
    frames = {}

    # Create instances of the different frames
    for F in (LoginFrame, MonitoringFrame):
        frame = F(parent=root, controller=root, activity_monitor=activity_monitor)
        frames[F] = frame
        frame.grid(row=0, column=0, sticky="nsew")

    # This function helps in switching between frames
    def show_frame(frame_class):
        frame = frames[frame_class]
        frame.tkraise()

    root.show_frame = show_frame

    # Initially show the LoginFrame
    show_frame(LoginFrame)
