from threading import Thread, Event, Lock
import threading
import queue
import time
from datetime import datetime
import getpass
import tkinter as tk
from pynput import keyboard, mouse
import pygetwindow as gw
import json
import cv2
from gaze_predictor import GazePredictor
from focus_predictor import FocusPredictor
import os
class ActivityMonitor:
    MOUSE_MOVE_THROTTLE = 0.5
    ASK_FOCUS_LEVEL_INTERVAL = 30 * 60
    KEYBOARD_SESSION_TIMEOUT = 1
    GAZE_MONITOR_INTERVAL = 0.3

    def __init__(self):
        self.user_id = getpass.getuser()
        self.monitoring_active = Event()
        self.monitoring_active.set()
        self.event_queue = queue.Queue()
        self.event_queue_lock = Lock()
        self.last_mouse_event_time = time.time()
        self.last_event_time = None
        self.mouse_start_position = None
        self.keyboard_activity_buffer = []
        self.last_keyboard_activity_time = None 
        self.window_activity_thread = None
        self.gaze_start_time = None
        self.gaze_start_position = None
        self.keyboard_session_active = False
        self.focus_predictor = FocusPredictor('./models/model.h5','./models/encoder.pkl', './models/scaler.pkl')
        self.prediction_thread = None
        self.gaze_predictor = GazePredictor(
            model_path='./models/eye_gaze_v31_20.h5',
            adjustment_model_path='./models/adjustment_model.h5',
            shape_predictor_path='./models/shape_predictor_68_face_landmarks.dat',
        )

    def log_event(self, event_type, data):
        current_time = datetime.now()
        timestamp = current_time.isoformat()
        event = {
            "timestamp": timestamp, 
            "type": event_type, 
            "data": data, 
            "time_delta": None  # Initialize time_delta with None
        }
        with self.event_queue_lock:
            if self.last_event_time is not None:
                event['time_delta'] = (current_time - self.last_event_time).total_seconds()
            self.last_event_time = current_time  # Update the last event time
            self.event_queue.put(event)

    def on_press(self, key):
        if not self.monitoring_active.is_set():
            return False
        current_time = time.time()
        if not self.keyboard_activity_buffer or current_time - self.last_keyboard_activity_time > self.KEYBOARD_SESSION_TIMEOUT:
            # If a new session or previous session has ended, log the old session if it exists
            if self.keyboard_activity_buffer:
                self.end_keyboard_session()
            self.keyboard_activity_buffer = [{"timestamp": datetime.now().isoformat(), "key": str(key)}]
        else:
            # Within the same session, append the key press
            self.keyboard_activity_buffer.append({"timestamp": datetime.now().isoformat(), "key": str(key)})
        self.last_keyboard_activity_time = current_time
        self.keyboard_session_active = True
        # Cancel existing timer if one is already set
        if hasattr(self, 'keyboard_session_timer'):
            self.keyboard_session_timer.cancel()
        # Set a new timer to end the session after the timeout period
        self.keyboard_session_timer = threading.Timer(self.KEYBOARD_SESSION_TIMEOUT, self.end_keyboard_session)
        self.keyboard_session_timer.start()

    def end_keyboard_session(self):
        if self.keyboard_activity_buffer:
            # Log the session
            self.log_event('keyboard_session', {
                'start_time': self.keyboard_activity_buffer[0]["timestamp"],
                'end_time': self.keyboard_activity_buffer[-1]["timestamp"],
                'key_strokes': len(self.keyboard_activity_buffer)
            })
            self.keyboard_activity_buffer = []  # Clear the session buffer
        self.keyboard_session_active = False  # Indicate the session has ended

    def on_click(self, x, y, button, pressed):
        if not self.monitoring_active.is_set():
            return False
        if pressed:
            self.log_event('mouse_click', {'position': (x, y), 'button': str(button)})
            self.mouse_start_position = (x, y)
        else:
            if self.mouse_start_position:
                self.log_event('mouse_movement', {'start_position': self.mouse_start_position, 'end_position': (x, y)})
                self.mouse_start_position = None

    def on_move(self, x, y):
        if not self.monitoring_active.is_set():
            return False
        current_time = time.time()
        if current_time - self.last_mouse_event_time >= self.MOUSE_MOVE_THROTTLE:
            if not self.mouse_start_position:
                self.mouse_start_position = (x, y)
            self.last_mouse_event_time = current_time

    def log_active_window_periodically(self):
        last_active_window_title = None
        while self.monitoring_active.is_set():
            active_window_title = gw.getActiveWindow().title if gw.getActiveWindow() else None
            if active_window_title and active_window_title != last_active_window_title:
                self.log_event("active_window", {"title": active_window_title})
                last_active_window_title = active_window_title
            time.sleep(2)

    def monitor_gaze(self):
        cap = cv2.VideoCapture(0)
        while self.monitoring_active.is_set():
            ret, frame = cap.read()
            if not ret:
                break

            gaze_x, gaze_y, adjusted_x, adjusted_y = self.gaze_predictor.predict_gaze(frame)
            if gaze_x is not None:
                self.gaze_start_position = (adjusted_x, adjusted_y)

                log_data = {
                    "gaze_start_position": (gaze_x, gaze_y),
                    "adjusted_gaze_start_position": (adjusted_x, adjusted_y)
                }
                self.log_event("gaze_data", log_data)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        cap.release()

    def ask_focus_level(self):
        while self.monitoring_active.is_set():
            time.sleep(self.ASK_FOCUS_LEVEL_INTERVAL)
            while self.keyboard_session_active:
                time.sleep(0.5)
            root = tk.Tk()
            root.attributes('-topmost', True)
            root.focus_force()
            root.title("Focus Level")

            def on_submit():
                focus_level = scale.get()
                self.log_event('focus_level', {'level': focus_level})
                root.destroy()
                self.periodic_data_saving()

            tk.Label(root, text="Rate your focus level:").pack()
            scale = tk.Scale(root, from_=0, to=10, orient='horizontal')
            scale.pack()
            tk.Button(root, text="Submit", command=on_submit).pack()

            root.mainloop()

    def save_events_to_temp_json(self):
        """ Saves events to a temporary JSON file for intermediate storage. """
        event_batch = []
        with self.event_queue_lock:
            while not self.event_queue.empty():
                event = self.event_queue.get_nowait()
                event_batch.append(event)
        
        if event_batch:
            try:
                print(event_batch)
                with open("./temp.js", "w") as file:
                    json.dump(event_batch, file, indent=4)
            except Exception as e:
                print(f"Failed to write to {self.temp_data_path}: {e}")

    def periodic_process_and_save(self):
        """ Periodically processes events for prediction and saves them to the final JSON file every minute. """
        while self.monitoring_active.is_set():
            time.sleep(60)  # Ensure this runs every 60 seconds
            
            self.save_events_to_temp_json()  # Save current events to temp.json

            # Load and process the accumulated data
            if os.path.exists("./temp.json"):
                preds = self.focus_predictor.predict_focus("./temp.json")
                self.focus_predictor.print_results(preds)
            # Clear the temporary file to prepare for new data
            open(".temp.json", 'w').close()


    # def append_to_final_json(self, data, predictions):
    #     """ Appends processed data and predictions to the final JSON file. """
    #     try:
    #         with open(self.final_data_path, "r") as file:
    #             existing_data = json.load(file)
    #     except (FileNotFoundError, json.JSONDecodeError):
    #         existing_data = []

    #     # Convert numpy arrays to lists for JSON serialization
    #     updated_data = existing_data + [{"data": [d.tolist() for d in data], "predictions": [p.tolist() for p in predictions]}]

    #     try:
    #         with open(self.final_data_path, "w") as file:
    #             json.dump(updated_data, file, indent=4)
    #     except IOError as e:
    #         print(f"Failed to append to {self.final_data_path}: {e}")


    def start_monitoring(self):
        self.keyboard_listener = keyboard.Listener(on_press=self.on_press)
        self.mouse_listener = mouse.Listener(on_click=self.on_click, on_move=self.on_move)
        
        self.keyboard_listener.start()
        self.mouse_listener.start()

        self.process_and_save_thread = Thread(target=self.periodic_process_and_save, daemon=True)
        self.process_and_save_thread.start()
        
        self.gaze_monitoring_thread = Thread(target=self.monitor_gaze, daemon=True)
        self.gaze_monitoring_thread.start()

    def stop_monitoring(self):
        self.monitoring_active.clear()
        self.keyboard_listener.stop()
        self.mouse_listener.stop()