import os
import requests
from tkinter import messagebox

def has_been_calibrated(username):
    # Check if a file exists indicating the user has been calibrated
    return os.path.exists(f'calibration_{username}.txt')

def mark_as_calibrated(username):
    # Create a file to mark the user as calibrated
    with open(f'calibration_{username}.txt', 'w') as f:
        f.write('calibrated')

def register_user(username, password):
    try:
        response = requests.post("http://localhost:5000/register", json={"username": username, "password": password})
        if response.ok:
            messagebox.showinfo("Register", "Registration Successful")
        else:
            messagebox.showerror("Register", "Registration Failed")
    except requests.RequestException as e:
        messagebox.showerror("Register", str(e))

def login_user(username, password):
    try:
        response = requests.post("http://localhost:5000/login", json={"username": username, "password": password})
        if response.ok:
            messagebox.showinfo("Login", "Login Successful")
            return True  # Return True if login is successful
        else:
            messagebox.showerror("Login", "Login Failed")
            return False  # Return False if login is unsuccessful
    except requests.RequestException as e:
        messagebox.showerror("Login", str(e))
        return False  # Return False if an exception occurs

def predict_gaze(image_data):
    # This function should handle image data accordingly.
    pass
