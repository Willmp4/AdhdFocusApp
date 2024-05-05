import tkinter as tk
from tkinter import messagebox
import pyautogui as pag
from api import register_user, login_user, has_been_calibrated, mark_as_calibrated
from frontend.app.calibration_component import CalibrationComponent
from gui import show_frame

from sklearn.ensemble import RandomForestRegressor
from sklearn.externals import joblib
import numpy as np
import os
from PIL import Image

def extract_features(image_path):
    img = Image.open(image_path)
    return np.array(img).flatten()  # Simplified feature extraction

def load_data(calibration_folder):
    features = []
    labels = []
    for filename in os.listdir(calibration_folder):
        if filename.endswith('.png'):
            image_path = os.path.join(calibration_folder, filename)
            coords = tuple(map(int, filename.replace("calibration_point_", "").replace(".png", "").split('_')))
            feature = extract_features(image_path)
            features.append(feature)
            labels.append(coords)
    return np.array(features), np.array(labels)

def update_model(username, model_path='eye_gaze_model.pkl'):
    calibration_folder = f'calibration_data_{username}'  # Folder for user-specific calibration data
    model = joblib.load(model_path) if os.path.exists(model_path) else RandomForestRegressor(n_estimators=100)
    
    features, labels = load_data(calibration_folder)
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
        # Assuming the calibration logic is encapsulated as described
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
