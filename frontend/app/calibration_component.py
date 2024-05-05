import tkinter as tk
import pyautogui as pag
from PIL import Image

class CalibrationComponent:
    def __init__(self, root, on_calibration_complete):
        self.root = root
        self.on_calibration_complete = on_calibration_complete
        self.screen_width, self.screen_height = pag.size()
        self.calibration_points = []
        self.current_point = 0
        self.calibration_dot = None

        self.generate_calibration_points()
        self.display_point()
        self.root.bind('<space>', self.handle_spacebar)

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

    def capture_and_save_image(self):
        # Capture screen and save the image
        screenshot = pag.screenshot()
        filename = f"calibration_point_{self.current_point}.png"
        screenshot.save(filename)
        print(f"Saved screenshot at {filename} with coordinates {self.calibration_points[self.current_point]}")

    def handle_spacebar(self, event):
        self.capture_and_save_image()  # Capture and save the image when spacebar is pressed
        self.current_point += 1
        if self.current_point >= len(self.calibration_points):
            self.on_calibration_complete()
        else:
            self.display_point()

def on_calibration_complete():
    print("Calibration complete!")

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Calibration Component")
    root.geometry(f"{pag.size()[0]}x{pag.size()[1]}")
    app = CalibrationComponent(root, on_calibration_complete)
    root.mainloop()
