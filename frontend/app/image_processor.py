import tkinter as tk
import pyautogui as pag
from PIL import Image
import cv2
import numpy as np
import pickle

class ImageProcessor:
    def __init__(self, detector, predictor):
        self.detector = detector
        self.predictor = predictor

    def extract_eye_region(self, image, landmarks, left_eye_points, right_eye_points, nose_bridge_points, forehead_points):
        eye_points = left_eye_points + right_eye_points
        all_points = eye_points + nose_bridge_points + forehead_points
        region = np.array([(landmarks.part(point).x, landmarks.part(point).y) for point in all_points])
        min_x = np.min(region[:, 0])
        max_x = np.max(region[:, 0])
        min_y = np.min(region[:, 1])
        max_y = np.max(region[:, 1])
        cropped_region = image[min_y:max_y, min_x:max_x]
        return cropped_region

    def get_combined_eyes(self, frame, global_detector, global_predictor, target_size=(200, 100)):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = global_detector(gray)
        for face in faces:
            landmarks = global_predictor(gray, face)
            forehead_points = [20, 21, 22, 23, 0, 16]
            left_eye_landmarks = [36, 37, 38, 39, 40, 41]
            right_eye_landmarks = [42, 43, 44, 45, 46, 47]
            nose_bridge_points = [27, 28, 29]
            combined_eye_region = self.extract_eye_region(
                frame, landmarks, left_eye_landmarks, right_eye_landmarks, nose_bridge_points, forehead_points)
            combined_eye_region = cv2.resize(combined_eye_region, target_size, interpolation=cv2.INTER_AREA)
            combined_eye_region = combined_eye_region.astype(np.float32) / 255.0
            return combined_eye_region
        return None