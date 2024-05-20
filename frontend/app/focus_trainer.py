import os
import json
import numpy as np
import pickle
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.models import load_model
class FocusTrainer:
    def __init__(self, model_path, encoder_path, scaler_path):
        self.model_path = model_path
        self.encoder_path = encoder_path
        self.scaler_path = scaler_path

    def load_pickle(self, path):
        with open(path, 'rb') as f:
            return pickle.load(f)

    def load_json_data(self, file_path):
        session_data = []
        if os.path.isfile(file_path):
            print(f"Loading data from {file_path}")
            with open(file_path, 'r') as file:
                data = json.load(file)
                print(data)
                session_data.append(data)
        else:
            raise FileNotFoundError(f"The file {file_path} does not exist.")
        return session_data

    def preprocess_data(self, session_data, threshold=5):
        all_features = []
        all_labels = []
        for session in session_data:
            features = []
            label = None
            if not any('focus_level' in event['type'] for event in session):
                print("No focus level events found in the session.")
                continue
            for event in session:
                if 'focus_level' in event['type']:
                    focus_level = event['data']['level']
                    label = 1 if focus_level > threshold else 0
                    if features and label is not None:
                        all_features.append(features)
                        all_labels.append(label)
                    features = []
                else:
                    event_type = event['type']
                    if event_type == 'active_window':
                        continue
                    time_delta = event.get('time_delta', event['data'].get('time_delta', 0))
                    if event_type == 'gaze_data':
                        position = event['data'].get('adjusted_gaze_start_position', [0, 0])
                    elif event_type == 'mouse_movement':
                        start_position = event['data'].get('start_position', [0, 0])
                        end_position = event['data'].get('end_position', [0, 0])
                        position = [(s + e) / 2 for s, e in zip(start_position, end_position)]
                    elif event_type == 'mouse_click':
                        position = event['data'].get('position', [0, 0])
                    elif event_type == 'keyboard_session':
                        start_time = event['data'].get('start_time', event['timestamp'])
                        end_time = event['data'].get('end_time', event['timestamp'])
                        duration = (np.datetime64(end_time) - np.datetime64(start_time)).astype('timedelta64[ms]').astype(int)
                        position = [duration, 0]
                    else:
                        position = [0, 0]
                    button = event['data'].get('button', 'None')
                    feature = [event['timestamp'], event_type, position, button, time_delta]
                    features.append(feature)
        return all_features, all_labels

    def encode_features(self, features, encoder, scaler):
        all_categories = []
        all_time_deltas = []
        for session in features:
            all_categories.extend([[feat[1], feat[3]] for feat in session])
            all_time_deltas.extend([feat[4] for feat in session])

        all_time_deltas = np.array(all_time_deltas).reshape(-1, 1)
        all_time_deltas_normalized = scaler.transform(all_time_deltas).flatten()

        all_sessions = []
        time_delta_index = 0
        for session in features:
            categorical_features = np.array([[feat[1], feat[3]] for feat in session])
            categorical_encoded = encoder.transform(categorical_features).toarray()
            position_data = np.array([feat[2] for feat in session])
            time_deltas = np.array([all_time_deltas_normalized[time_delta_index:time_delta_index+len(session)]])
            time_delta_index += len(session)
            encoded_session = np.hstack((position_data, categorical_encoded, time_deltas.T))
            all_sessions.append(encoded_session)

        return all_sessions

    def create_sequences(self, features, labels, sequence_length=100):
        padded_features = pad_sequences(features, maxlen=sequence_length, padding='post', dtype='float32')
        padded_labels = np.array(labels)
        return padded_features, padded_labels

    def retrain_model(self, json_file_path):
        session_data = self.load_json_data(json_file_path)
        features, labels = self.preprocess_data(session_data)
        if not features:
            print("No valid data to train.")
            return

        # Load existing encoder and scaler
        encoder = self.load_pickle(self.encoder_path)
        scaler = self.load_pickle(self.scaler_path)
        
        encoded_features = self.encode_features(features, encoder, scaler)
        X, y = self.create_sequences(encoded_features, labels)

        # Load the existing model
        model = load_model(self.model_path)

        # Ensure input shape matches
        if model.input_shape[1:] != X.shape[1:]:
            raise ValueError(f"Model input shape {model.input_shape[1:]} does not match data shape {X.shape[1:]}.")

        model.fit(X, y, epochs=10, batch_size=32)
        

        # Save the retrained model and preprocessors
        self.save_model_and_preprocessors(model, encoder, scaler)
        print("Model retrained and saved.")
        open(json_file_path, 'w').close()

    def save_model_and_preprocessors(self, model, encoder, scaler):
        model.save(self.model_path)
        with open(self.encoder_path, 'wb') as f:
            pickle.dump(encoder, f)
        with open(self.scaler_path, 'wb') as f:
            pickle.dump(scaler, f)
