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

app = Flask(__name__)
CORS(app)

def get_raw_entry(n):
    database_handler = dbhandler.DatabaseHandler("../db-handler/dataset.db")
    last_entries = database_handler.get_last_entries("live_dataset", n)
    database_handler.close()
    data = {}
    for entry in last_entries:
        data = {
            "datetime": entry[0],
            "temperature": entry[1],
            "relative_humidity": entry[2],
            "rain": entry[3],
            "surface_pressure": entry[4],
            "soil_moisture": entry[5]
        }
    return data

def get_prediction_entry(n):
    database_handler = dbhandler.DatabaseHandler("../db-handler/dataset.db")
    last_entries = database_handler.get_last_entries("predictions", n)
    database_handler.close()
    data = {}
    for entry in last_entries:
        data = {
            "datetime": entry[0],
            "prediction_24": entry[1],
            "prediction_48": entry[2]
        }
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
def raw():
    raw_data = get_raw_entry(1)
    return jsonify(raw_data)

@app.route('/prediction')
def prediction():
    prediction_data = get_prediction_entry(1)
    return jsonify(prediction_data)

@app.route('/newdata', methods=['POST'])
def update_data():
    print("[DEBUG]: /newdata endpoint called")
    data = request.json
    print("[DEBUG]: Received data:", data)

    # Fetch rainfall and soil moisture from Open-Meteo API using the imported function
    total_rainfall, avg_soil_moisture = get_previous_day_weather()
    print("[DEBUG]: Open-Meteo API data - Rainfall:", total_rainfall, "Soil Moisture:", avg_soil_moisture)

    # Extract sensor data from request
    temperature = data.get("temperature")
    relative_humidity = data.get("relative_humidity")
    surface_pressure = data.get("surface_pressure")

    # Combine sensor and API data
    new_entry = {
        "temperature": temperature,
        "relative_humidity": relative_humidity,
        "rain": total_rainfall,
        "surface_pressure": surface_pressure,
        "soil_moisture": avg_soil_moisture
    }
    print("[DEBUG]: Combined data:", new_entry)

    # Update the dataset in the database
    try:
        database_handler = dbhandler.DatabaseHandler("../db-handler/dataset.db")
        print("[DEBUG]: DatabaseHandler initialized")
        database_handler.update_dataset("live_dataset", (
            temperature,
            relative_humidity,
            total_rainfall,
            surface_pressure,
            avg_soil_moisture
        ))
        print("[DEBUG]: Dataset updated successfully")
        database_handler.close()
    except Exception as e:
        print("[ERROR]:", str(e))
        return jsonify({"status": "error", "message": str(e)}), 500

    return jsonify({"status": "Data updated successfully", "data": new_entry}), 200
if __name__ == '__main__':
    app.run(debug=True)
