import os
import json
import numpy as np
import pickle
from sklearn.preprocessing import OneHotEncoder
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import LSTM, Dense, Dropout, Bidirectional, BatchNormalization
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split

class FocusTrainer:
    def __init__(self, model_path, encoder_path, scaler_path):
        self.model_path = model_path
        self.encoder_path = encoder_path
        self.scaler_path = scaler_path

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

    def preprocess_data(self, session_data, threshold=5):
        all_features = []
        all_labels = []
        for session in session_data:
            features = []
            label = None
            for event in session:
                # Check if the event is a focus level event and extract 
                if 'focus_level' in event['type']:
                    focus_level = event['data']['level']
                    label = 1 if focus_level > threshold else 0
                    if features and label is not None:  # Ensure there is data to add before resetting
                        all_features.append(features)
                        all_labels.append(label)
                    # Reset features and label for a new session starting after this event
                    features = []
                # Extract features based on event type
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
                        position = [(s + e) / 2 for s, e in zip(start_position, end_position)]  # Average position
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

    def encode_features(self, features):
        all_categories = []
        all_time_deltas = []
        for session in features:
            all_categories.extend([[feat[1], feat[3]] for feat in session])
            all_time_deltas.extend([feat[4] for feat in session])

        encoder = OneHotEncoder()
        encoder.fit(all_categories)

        scaler = StandardScaler()
        all_time_deltas = np.array(all_time_deltas).reshape(-1, 1)
        scaler.fit(all_time_deltas)
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

        return all_sessions, encoder, scaler

    def create_sequences(self, features, labels, sequence_length=100):
        # Padding sequences
        padded_features = pad_sequences(features, maxlen=sequence_length, padding='post', dtype='float32')
        padded_labels = np.array(labels)  # No need to pad labels as there is one per sequence
        return padded_features, padded_labels

    def build_and_train_model(self, X_train, y_train, X_test, y_test):
        # Convert lists to numpy arrays if not already
        X_train = np.array(X_train)
        y_train = np.array(y_train)
        X_test = np.array(X_test)
        y_test = np.array(y_test)
        
        # Check if sequences array is not empty
        if X_train.size > 0:
            model = Sequential()
            
            # Add bidirectional LSTMs and more layers
            model.add(Bidirectional(LSTM(128, return_sequences=True, input_shape=(X_train.shape[1], X_train.shape[2]))))
            model.add(BatchNormalization())
            model.add(Dropout(0.2))
            model.add(Bidirectional(LSTM(128, return_sequences=True)))
            model.add(Dropout(0.2))
            model.add(Bidirectional(LSTM(84)))
            model.add(Dropout(0.2))
            

            # Add dense layers
            model.add(Dense(128, activation='relu'))
            model.add(Dense(64, activation='relu'))
            model.add(Dense(32, activation='relu'))
            model.add(Dense(1, activation='sigmoid'))
            
            # Compile the model with an optimizer and loss function
            model.compile(loss='binary_crossentropy', optimizer='adam', metrics=['accuracy'])
            
            # Train the model
            model.fit(X_train, y_train, epochs=5, batch_size=64, validation_data=(X_test, y_test))
            return model
        else:
            print("No valid sequences to train on.")
            return None

    def retrain_model(self, json_file_path):
        session_data = self.load_json_data(json_file_path)
        features, labels = self.preprocess_data(session_data)
        if not features:
            print("No valid data to train.")
            return

        encoded_features, encoder, scaler = self.encode_features(features)
        X, y = self.create_sequences(encoded_features, labels)

        # Split the data into training and testing sets
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        # Load the existing model
        model = load_model(self.model_path)

        # Retrain the model
        model = self.build_and_train_model(X_train, y_train, X_test, y_test)

        # Save the retrained model and preprocessors
        if model:
            self.save_model_and_preprocessors(model, encoder, scaler)
            print("Model retrained and saved.")
            # Clear final.json
            open(json_file_path, 'w').close()

    def save_model_and_preprocessors(self, model, encoder, scaler):
        # Save the Keras model
        model.save(self.model_path)
        # Save the preprocessors
        with open(self.encoder_path, 'wb') as f:
            pickle.dump(encoder, f)
        with open(self.scaler_path, 'wb') as f:
            pickle.dump(scaler, f)
