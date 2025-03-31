from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import os

# Add paths to other modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../db-handler')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../predictor')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../open-meteo')))  

import predictor
import dbhandler
from rain_soil import get_previous_day_weather  # Import the function
from rain_soil import get_previous_hour_weather  # Import the function
from predictor import predict_flood_hourly
app = Flask(__name__)
CORS(app)

def get_raw_entry(n):
    database_handler = dbhandler.DatabaseHandler("../db-handler/dataset.db")
    last_entries = database_handler.get_last_entries("live_dataset", n)
    database_handler.close()
    data = []
    for entry in last_entries:
        data.append({
            "datetime": entry[0],
            "temperature": entry[1],
            "relative_humidity": entry[2],
            "rain": entry[3],
            "surface_pressure": entry[4],
            "soil_moisture": entry[5]
        })
    return data

def get_prediction_entry(n):
    database_handler = dbhandler.DatabaseHandler("../db-handler/dataset.db")
    last_entries = database_handler.get_last_entries("predictions", n)
    database_handler.close()
    data = []
    for entry in last_entries:
        data.append({
            "datetime": entry[0],
            "prediction_24": entry[1],
            "prediction_48": entry[2]
        })
    return data
    
@app.before_request
def logger():
    print("___________________________")
    print("URL", request.base_url)
    print("Headers:", request.headers)
    print("Base Path: ", request.base_url)
    # print("Body: ", request.get_data())
    print("---------------------------")

@app.route('/raw')
@app.route('/raw/<int:n>')
def raw(n=1):
    raw_data = get_raw_entry(n)
    return jsonify(raw_data)

@app.route('/prediction')
@app.route('/prediction/<int:n>')
def prediction(n=1):
    prediction_data = get_prediction_entry(n)
    return jsonify(prediction_data)

@app.route('/newdata', methods=['POST'])
def update_data():
    print("[DEBUG]: /newdata endpoint called")
    data = request.json
    print("[DEBUG]: Received data:", data)

    # Fetch rainfall and soil moisture from Open-Meteo API using the imported function
    previous_rain, previous_soil_moisture = get_previous_hour_weather()
    print("[DEBUG]: Open-Meteo API data - Rainfall:", previous_rain, "Soil Moisture:", previous_soil_moisture)

    # Extract sensor data from request
    temperature = data.get("temperature")
    relative_humidity = data.get("relative_humidity")
    surface_pressure = data.get("surface_pressure")

    # Combine sensor and API data
    new_entry = {
        "temperature": temperature,
        "relative_humidity": relative_humidity,
        "rain": previous_rain,
        "surface_pressure": surface_pressure,
        "soil_moisture": previous_soil_moisture
    }
    print("[DEBUG]: Combined data:", new_entry)

    # Update the dataset in the database
    try:
        database_handler = dbhandler.DatabaseHandler("../db-handler/dataset.db")
        print("[DEBUG]: DatabaseHandler initialized")
        
        # Step 1: Update hourly_data table
        database_handler.update_dataset("hourly_data", (
            temperature,
            relative_humidity,
            previous_rain,
            surface_pressure,
            previous_soil_moisture
        ))
        print("[DEBUG]: hourly_data table updated successfully")

        # Step 2: Perform prediction on the hourly data
        prediction_24, prediction_48 = predict_flood_hourly()
        print("[DEBUG]: Predictions - 24-hour:", prediction_24, "48-hour:", prediction_48)

        # Step 3: Update hourly_predictions table with new predictions
        database_handler.update_predictions("hourly_predictions", (prediction_24, prediction_48))
        print("[DEBUG]: hourly_predictions table updated successfully")

        # Close the database connection
        database_handler.close()
    except Exception as e:
        print("[ERROR]:", str(e))
        return jsonify({"status": "error", "message": str(e)}), 500

    return jsonify({
        "status": "success",
        "message": "Data and predictions updated successfully",
        "data": new_entry,
        "predictions": {
            "24_hour": prediction_24,
        }
    }), 200
if __name__ == '__main__':
    
    app.run(debug=True)