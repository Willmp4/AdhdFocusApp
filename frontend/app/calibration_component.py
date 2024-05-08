import tkinter as tk
import pyautogui as pag
from PIL import Image
import cv2
import pickle
import numpy as np
from image_processor import ImageProcessor

class CalibrationComponent:
    def __init__(self, root, on_calibration_complete, image_processor):
        self.root = root
        self.on_calibration_complete = on_calibration_complete
        self.image_processor = image_processor
        self.screen_width, self.screen_height = pag.size()
        self.calibration_points = []
        self.current_point = 0
        self.calibration_dot = None
        self.data_X = []  # List to store images
        self.data_y = []  # List to store gaze coordinates
        self.generate_calibration_points()
        self.display_point()
        self.root.bind('<space>', self.handle_spacebar)
        self.root.bind('<F11>', self.toggle_fullscreen)
        self.root.attributes('-fullscreen', True)
        # Initialize the webcam
        self.cap = cv2.VideoCapture(0)  # Argument is the index of the webcam

    def generate_calibration_points(self):
        offset = 20
        points = [
            (offset, offset),
            (offset, self.screen_height - offset),
            (self.screen_width - offset, self.screen_height - offset),
            (self.screen_width - offset, offset)
        ]
        num_central_points = 46
        central_points_per_side = round(num_central_points ** 0.5)
        step_x = (self.screen_width - 2 * offset) / (central_points_per_side + 1)
        step_y = (self.screen_height - 2 * offset) / (central_points_per_side + 1)
        for i in range(1, central_points_per_side + 1):
            for j in range(1, central_points_per_side + 1):
                x = round(offset + i * step_x)
                y = round(offset + j * step_y)
                points.append((x, y))
        self.calibration_points = points

    def display_point(self):
        if self.calibration_dot:
            self.calibration_dot.destroy()
        if self.current_point < len(self.calibration_points):
            x, y = self.calibration_points[self.current_point]
            self.calibration_dot = tk.Label(self.root, text='O', font=('Helvetica', 24), fg='red')
            self.calibration_dot.place(x=x, y=y)
        else:
            self.on_calibration_complete()

    def capture_and_process_image(self):
        # Capture image from the webcam
        ret, frame = self.cap.read()
        if not ret:
            print("Failed to capture image from webcam")
            return None, None
        processed_image = self.image_processor.get_combined_eyes(frame, self.image_processor.detector, self.image_processor.predictor)
        return processed_image, self.calibration_points[self.current_point]

    def handle_spacebar(self, event):
        processed_image, gaze_coords = self.capture_and_process_image()
        if processed_image is not None:
            self.data_X.append(processed_image)
            self.data_y.append(gaze_coords)
            self.current_point += 1
            if self.current_point >= len(self.calibration_points):
                self.save_data()
                self.on_calibration_complete()
                self.cap.release()  # Release the webcam resource
            else:
                self.display_point()

    def save_data(self):
        # Save all collected data to a pickle file
        calibration_data = {'images': self.data_X, 'gaze_coords': self.data_y}
        with open('calibration_data.pkl', 'wb') as f:
            pickle.dump(calibration_data, f)
        print("Data saved to calibration_data.pkl")

def on_calibration_complete():
    print("Calibration complete!")
    root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Calibration Component")
    root.geometry(f"{pag.size()[0]}x{pag.size()[1]}")
    # Here you need to initialize your detector and predictor
    detector = None  # Initialize your face detector here
    predictor = None  # Initialize your landmark predictor here
    image_processor = ImageProcessor(detector, predictor)
    app = CalibrationComponent(root, on_calibration_complete, image_processor)
    root.mainloop()
