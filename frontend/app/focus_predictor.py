import os
import json
import numpy as np
import pickle
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.sequence import pad_sequences
class FocusPredictor:
    def __init__(self, model_path, encoder_path, scaler_path):
        self.model = load_model(model_path)
        self.encoder = self.load_pickle(encoder_path)
        self.scaler = self.load_pickle(scaler_path)

    def load_pickle(self, path):
        with open(path, 'rb') as f:
            return pickle.load(f)

    def load_json_data(self, file_path):
        if os.path.isfile(file_path):
            print(f"Loading data from {file_path}")
            with open(file_path, 'r') as file:
                return json.load(file)
        else:
            raise FileNotFoundError(f"The file {file_path} does not exist.")

    def preprocess_data(self, session_data):
        features = []
        for event in session_data:
            event_type = event.get('type')
            if event_type not in ['gaze_data', 'mouse_movement', 'mouse_click', 'keyboard_session']:
                continue

            time_delta = event.get('time_delta', event['data'].get('time_delta', 0))
            feature_data = [0, 0]  # Default values for positions

            if event_type == 'gaze_data':
                feature_data = event['data'].get('adjusted_gaze_start_position', [0, 0])
            elif event_type == 'mouse_movement':
                start_position = event['data'].get('start_position', [0, 0])
                end_position = event['data'].get('end_position', [0, 0])
                feature_data = [(s + e) / 2 for s, e in zip(start_position, end_position)]
            elif event_type == 'mouse_click':
                feature_data = event['data'].get('position', [0, 0])
            elif event_type == 'keyboard_session':
                start_time = event['data'].get('start_time', event['timestamp'])
                end_time = event['data'].get('end_time', event['timestamp'])
                duration = (np.datetime64(end_time) - np.datetime64(start_time)).astype('timedelta64[ms]').astype(int)
                feature_data = [duration, 0] 
            button = event['data'].get('button', 'None')
            features.append([event['timestamp'], event_type, feature_data, button, time_delta])

        return features

    def encode_and_scale_features(self, features):
        categorical_data = np.array([[feat[1], feat[3]] for feat in features])
        positions = np.array([feat[2] for feat in features])
        time_deltas = np.array([[feat[4]] for feat in features])

        # Normalize time deltas
        time_deltas = self.scaler.transform(time_deltas)

        # Encode categorical data
        categorical_encoded = self.encoder.transform(categorical_data).toarray()

        # Combine all features
        encoded_features = np.hstack((positions, categorical_encoded, time_deltas))
        return encoded_features

    def create_sequences(self, encoded_features, sequence_length=100):
        # Padding sequences to ensure they have the same length
        return pad_sequences([encoded_features], maxlen=sequence_length, padding='post', dtype='float32')

    def predict_focus(self, json_file_path):
        session_data = self.load_json_data(json_file_path)
        features = self.preprocess_data(session_data)
        if not features:
            return "No valid data to predict."

        encoded_features = self.encode_and_scale_features(features)
        sequences = self.create_sequences(encoded_features)
        predictions = self.model.predict(sequences)
        return predictions

    def print_results(self, predictions):
        for pred in predictions:
            print(f"Predicted Focus Level: {pred[0]:.2f}")