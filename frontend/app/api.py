import requests
from tkinter import messagebox

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
        else:
            messagebox.showerror("Login", "Login Failed")
    except requests.RequestException as e:
        messagebox.showerror("Login", str(e))

def predict_gaze(image_data):
    # This function should handle image data accordingly.
    pass
