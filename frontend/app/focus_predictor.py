import os
import json
import numpy as np
from sklearn.preprocessing import OneHotEncoder
from keras.models import load_model
from keras.preprocessing.sequence import pad_sequences
import joblib

class FocusPredictor:
    def __init__(self, model_path, encoder_path):
        self.model = load_model(model_path)
        self.encoder = joblib.load(encoder_path)

    def load_data(self, directory):
        session_data = []
        for user_folder in os.listdir(directory):
            print("Loading data for user", user_folder)
            user_path = os.path.join(directory, user_folder)
            if os.path.isdir(user_path):
                for date_folder in os.listdir(user_path):
                    print("Loading data for date", date_folder)
                    date_path = os.path.join(user_path, date_folder)
                    activity_file = 'events_data.json'
                    print("Loading data from", date_path)
                    file_path = os.path.join(date_path, activity_file)
                    if os.path.isfile(file_path):
                        with open(file_path, 'r') as file:
                            file_data = json.load(file)
                            if isinstance(file_data, list):
                                session_data.append(file_data)  # Each file is one session
        return session_data

    def preprocess_data(self, session_data, threshold=5):
        all_features = []
        all_labels = []
        for session in session_data:
            print("Processing session with", len(session), "events")
            features = []
            label = None
            for event in session:
                if 'focus_level' in event['type']:
                    focus_level = event['data']['level']
                    label = 1 if focus_level > threshold else 0
                    if features and label is not None:
                        print("Adding session with", len(features), "events")
                        all_features.append(features)
                        all_labels.append(label)
                    features = []
                else:
                    event_type = event['type']
                    position = self.extract_position(event)
                    button = event['data'].get('button', 'None')
                    feature = [event['timestamp'], event_type, position, button]
                    features.append(feature)
        return all_features, all_labels

    def extract_position(self, event):
        event_type = event['type']
        if event_type == 'gaze_data':
            position = event['data'].get('adjusted_gaze_start_position', [0, 0])
        elif event_type == 'mouse_movement':
            start_position = event['data'].get('start_position', [0, 0])
            end_position = event['data'].get('end_position', [0, 0])
            position = [(s + e) / 2 for s, e in zip(start_position, end_position)]
        elif event_type == 'mouse_click':
            position = event['data'].get('position', [0, 0])
        else:
            position = [0, 0]
        return position

    def encode_features(self, features):
        all_categories = [[feat[1], feat[3]] for session in features for feat in session]
        categorical_encoded = self.encoder.transform(all_categories).toarray()
        position_data = np.array([feat[2] for session in features for feat in session])
        encoded_features = np.hstack((position_data, categorical_encoded))
        return encoded_features.reshape(len(features), -1, encoded_features.shape[1])

    def create_sequences(self, features, labels, sequence_length=100):
        padded_features = pad_sequences(features, maxlen=sequence_length, padding='post', dtype='float32')
        padded_labels = np.array(labels)
        print(padded_features.shape, padded_labels.shape)
        return padded_features, padded_labels

    def predict_focus(self, encoded_features):
        predictions = self.model.predict(encoded_features)
        return predictions

    def print_results(self, predictions):
        for pred in predictions:
            print(f"Predicted Focus Level: {pred[0]:.2f}")

if __name__ == "__main__":
    predictor = FocusPredictor(model_path='path_to_your_model.h5', encoder_path='path_to_encoder.pkl')
    directory = '../../focus_level/'
    session_data = predictor.load_data(directory)
    if session_data:
        features, labels = predictor.preprocess_data(session_data)
        encoded_features = predictor.encode_features(features)
        sequences, sequence_labels = predictor.create_sequences(encoded_features, labels)
        predictions = predictor.predict_focus(sequences)
        predictor.print_results(predictions)
    else:
        print("No session data found")