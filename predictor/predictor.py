import numpy as np
import pandas as pd
import joblib
import os
import sys
from tensorflow.keras.models import load_model
import time

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../db-handler')))
import dbhandler

# Initialize the database handler
database_handler = dbhandler.DatabaseHandler("../db-handler/dataset.db")

# Load models
model_24 = load_model("../predictor/flood_prediction_24h.keras")
model_48 = load_model("../predictor/flood_prediction_48h.keras")

# Load scaler
scaler = joblib.load("../predictor/scaler.pkl")

def predict_flood():
    # Fetch the last 30 entries from the database
    prev_data = database_handler.get_last_entries("live_dataset", 30)
    if len(prev_data) < 30:
        print("[ERROR]: Not enough data in the database to make predictions. At least 30 entries are required.")
        return

    # Convert the data into a DataFrame
    prev_data = pd.DataFrame([entry[1:] for entry in prev_data])  # Exclude the datetime column

    # Scale the data
    scaled_input = scaler.transform(prev_data)

    # Reshape for LSTM input (1 sample, 30 timesteps, 5 features)
    lstm_input = scaled_input.reshape(1, 30, 5)

    # Make predictions
    prediction_24 = model_24.predict(lstm_input)
    prediction_48 = model_48.predict(lstm_input)

    # Determine risk levels
    level_24 = int(np.argmax(prediction_24))
    level_48 = int(np.argmax(prediction_48))

    # Log predictions
    print("[INFO]: 24-hour Prediction:", prediction_24)
    print("[INFO]: 48-hour Prediction:", prediction_48)
    print("[INFO]: 24-hour Risk Level:", level_24)
    print("[INFO]: 48-hour Risk Level:", level_48)

    # Update predictions in the database
    try:
        database_handler.update_predictions("predictions", (level_24, level_48))
        print("[INFO]: Predictions updated successfully in the database.")
    except Exception as e:
        print("[ERROR]: Failed to update predictions in the database:", str(e))

if __name__ == "__main__":
    predict_flood()