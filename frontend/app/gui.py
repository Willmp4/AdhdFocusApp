import tkinter as tk
from tkinter import messagebox
import pyautogui as pag
from api import register_user, login_user, has_been_calibrated, mark_as_calibrated
from calibration_component import CalibrationComponent
import numpy as np
import pickle
import os
import dlib
from image_processor import ImageProcessor
from desktop_activity import ActivityMonitor
from keras.models import load_model

def load_data(calibration_file):
    # Load calibration data from a pickle file
    with open(calibration_file, 'rb') as f:
        data = pickle.load(f)
    features = np.array(data['images'])
    labels = np.array(data['gaze_coords'])
    return features, labels

def gaze_predict(model_path='./models/eye_gaze_v31_20.h5', calibration_file='calibration_data.pkl'):
    features, labels = load_data(calibration_file)

    gaze_model = load_model(model_path)

    # Predict gaze points for each image in the calibration dataset
    predicted_gaze_points = []
    for image in features:
        image_reshaped = np.expand_dims(image, axis=0)
        predicted_point = gaze_model.predict(image_reshaped)[0][0]
        predicted_gaze_points.append(predicted_point)

    # Create the dataset for the adjustment model
    adjustment_dataset = {
        'predicted_gaze_points': predicted_gaze_points,
        'actual_gaze_points': labels
    }

    return adjustment_dataset

def save_model(model, model_path='./models/adjustment_model1.h5'):
    print("Saving model to", model_path)
    # Save the trained model to a file
    model.save(model_path)
    print("Model saved to", model_path)

def update_model(model_path='./models/adjustment_model.h5'):
    print("Loading existing model.")
    model = load_model(model_path)
    adjusment_dataset = gaze_predict()

    X = np.squeeze(np.array(adjusment_dataset['predicted_gaze_points']))  # Remove extra dimensions
    y = np.array(adjusment_dataset['actual_gaze_points'])[:, :2]  # Remove extra dimensions

    model.fit(X, y)
    save_model(model)
    print("Model updated and saved.")

class LoginFrame(tk.Frame):
    def __init__(self, parent, activity_monitor, show_frame):
        tk.Frame.__init__(self, parent)
        self.activity_monitor = activity_monitor
        self.show_frame = show_frame

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
                self.show_frame(MonitoringFrame)
        else:
            messagebox.showerror("Login failed", "The username or password is incorrect or an error occurred.")

    def launch_calibration(self, username):
        root = tk.Toplevel()
        root.title("Calibration Component")

        detector = dlib.get_frontal_face_detector()
        predictor = dlib.shape_predictor("./models/shape_predictor_68_face_landmarks.dat")

        image_processor = ImageProcessor(detector, predictor)
        root.geometry(f"{pag.size()[0]}x{pag.size()[1]}")

        app = CalibrationComponent(root, lambda: self.complete_calibration(username), image_processor)
        root.mainloop()

    def complete_calibration(self, username):
        mark_as_calibrated(username)
        update_model()  # Update the model with the new calibration data
        print("Calibration complete!")
        self.show_frame(MonitoringFrame)

class MonitoringFrame(tk.Frame):
    def __init__(self, parent, activity_monitor, show_frame):
        tk.Frame.__init__(self, parent)
        self.activity_monitor = activity_monitor
        self.show_frame = show_frame

        start_monitor_button = tk.Button(self, text="Start Monitoring", command=self.activity_monitor.start_monitoring)
        start_monitor_button.pack()

        logout_button = tk.Button(self, text="Logout", command=lambda: self.show_frame(LoginFrame))
        logout_button.pack()

def on_closing(activity_monitor):
    if messagebox.askokcancel("Quit", "Do you want to quit?"):
        activity_monitor.stop_monitoring()
        root.destroy()

def setup_gui(root, activity_monitor):
    # Create a dictionary to hold references to different frames
    frames = {}
    
    # This function helps in switching between frames
    def show_frame(frame_class):
        frame = frames[frame_class]
        frame.tkraise()

    # Create instances of the different frames
    for F in (LoginFrame, MonitoringFrame):
        frame = F(parent=root, activity_monitor=activity_monitor, show_frame=show_frame)
        frames[F] = frame
        frame.grid(row=0, column=0, sticky="nsew")

    root.show_frame = show_frame

    # Initially show the LoginFrame
    show_frame(LoginFrame)

# Create the main window
root = tk.Tk()
root.title("Focus Monitoring App")

# Create an instance of ActivityMonitor
activity_monitor = ActivityMonitor()

# Setup the GUI with the activity_monitor instance
setup_gui(root, activity_monitor)

# Set the protocol for closing the window
root.protocol("WM_DELETE_WINDOW", lambda: on_closing(activity_monitor))

# Start the main event loop
root.mainloop()
