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
    # Reinitialize the database connection to ensure it's fresh
    local_db_handler = dbhandler.DatabaseHandler("../db-handler/dataset.db")
    
    # Fetch the last 30 entries from the database
    prev_data = local_db_handler.get_last_entries("daily_data", 30)
    print(f"[DEBUG]: Number of entries fetched: {len(prev_data) if prev_data else 0}")
    
    if not prev_data or len(prev_data) < 30:
        print("[ERROR]: Not enough data in the database to make predictions. At least 30 entries are required.")
        local_db_handler.close()  # Close the connection
        return "Insufficient Data", "Insufficient Data"

    # Extract features correctly - exclude id and datetime columns
    feature_data = []
    for entry in prev_data:
        # Assuming entry structure is [id, datetime, temp, humid, rain, pressure, soil]
        feature_values = entry[2:7]  # Extract only the 5 feature columns
        feature_data.append(feature_values)
    
    # Convert to DataFrame for easier handling
    prev_data = pd.DataFrame(feature_data)
    print(f"[DEBUG]: DataFrame shape: {prev_data.shape}")

    # Validate we have exactly 5 features
    if prev_data.shape[1] != 5:
        print(f"[ERROR]: Wrong number of features. Expected 5, got {prev_data.shape[1]}.")
        local_db_handler.close()
        return "Feature Count Error", "Feature Count Error"

    # Scale the data
    try:
        scaled_input = scaler.transform(prev_data)
    except Exception as e:
        print(f"[ERROR]: Scaling error: {e}")
        local_db_handler.close()
        return f"Scaling Error: {str(e)}", f"Scaling Error: {str(e)}"

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

    # Close the database connection
    local_db_handler.close()
    
    # Just return the predictions - don't update the database here
    return level_24, level_48

    return level_24, level_48
def predict_flood_hourly():
    # Reinitialize the database connection to ensure it's fresh
    local_db_handler = dbhandler.DatabaseHandler("../db-handler/dataset.db")

    # Define thresholds
    THRESHOLDS = {
        "rain (mm)": [4.0, 13.0, 36.5],  # P60, P80, P95
        "relative_humidity_2m (%)": [86.125, 89.583, 92.625],  
        "soil_moisture_0_to_7cm (m³/m³)": [0.448917, 0.475250, 0.499250]
    }

    # Fetch the last 7 entries from the database
    prev_data = local_db_handler.get_last_entries("hourly_data", 7)
    print(f"[DEBUG]: Number of entries fetched: {len(prev_data) if prev_data else 0}")
    
    if not prev_data or len(prev_data) < 7:
        print("[ERROR]: Not enough data in the database to make predictions. At least 7 entries are required.")
        local_db_handler.close()
        return "Insufficient Data", "Insufficient Data"

    # Extract relevant features: [id, datetime, temp, humid, rain, pressure, soil]
    feature_data = []
    for entry in prev_data:
        feature_values = [entry[3], entry[4], entry[6]]  # Extract humidity, rain, soil moisture
        feature_data.append(feature_values)

    # Convert to DataFrame
    prev_data = pd.DataFrame(feature_data, columns=["relative_humidity_2m (%)", "rain (mm)", "soil_moisture_0_to_7cm (m³/m³)"])
    print(f"[DEBUG]: DataFrame shape: {prev_data.shape}")

    # Compute average values over the last 7 entries
    avg_values = prev_data.mean().to_dict()

    # Classify risk levels
    def classify_risk(value, thresholds):
        if value >= thresholds[2]:
            return 2  # High risk
        elif value >= thresholds[1]:
            return 1  # Medium risk
        elif value >= thresholds[0]:
            return 0  # Low risk
        return 0  # Default to Low risk if below all thresholds

    level_24 = max(classify_risk(avg_values[var], THRESHOLDS[var]) for var in THRESHOLDS)
    level_48 = level_24  # Keeping it the same since no trend analysis is involved

    # Log results
    print("[INFO]: 24-hour Risk Level:", level_24)
    print("[INFO]: 48-hour Risk Level:", level_48)

    # Close the database connection
    local_db_handler.close()
    
    return level_24, level_48
if __name__ == "__main__":
    predict_flood()