from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import os
from datetime import datetime
import time  # Add this import
# Add paths to other modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../db-handler')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../predictor')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../open-meteo')))  

import predictor
import dbhandler
from rain_soil import get_previous_day_weather  # Import the function
from rain_soil import get_previous_hour_weather  # Import the function
from predictor import predict_flood_hourly
from predictor import predict_flood
app = Flask(__name__)
CORS(app)

def get_raw_entry(n):
    database_handler = dbhandler.DatabaseHandler("../db-handler/dataset.db")
    last_entries = database_handler.get_last_entries("daily_data", n)  # Updated table name
    database_handler.close()
    data = []
    for entry in last_entries:
        data.append({
            "datetime": entry[1],  # Assuming datetime is the second column
            "temperature": entry[2],
            "relative_humidity": entry[3],
            "rain": entry[4],
            "surface_pressure": entry[5],
            "soil_moisture": entry[6]
        })
    return data



def get_prediction_entry(n):
    database_handler = dbhandler.DatabaseHandler("../db-handler/dataset.db")
    last_entries = database_handler.get_last_entries("daily_predictions", n)  # Updated table name
    database_handler.close()
    data = []
    for entry in last_entries:
        data.append({
            "datetime": entry[1],  # Assuming datetime is the second column
            "prediction_24": entry[2],
            "prediction_48": entry[3]
        })
    return data


def aggregate_hourly_to_daily():
    print("[DEBUG]: Aggregating hourly_data into daily_data")
    try:
        database_handler = dbhandler.DatabaseHandler("../db-handler/dataset.db")
        print("[DEBUG]: DatabaseHandler initialized")

        # Step 1: Fetch all hourly data for the current day
        current_date = datetime.now().strftime("%Y-%m-%d")
        start_of_day = int(datetime.strptime(current_date, "%Y-%m-%d").timestamp())
        end_of_day = start_of_day + 86400  # Add 24 hours in seconds

        hourly_data = database_handler.get_entries_in_range("hourly_data", start_of_day, end_of_day)
        print(f"[DEBUG]: Fetched {len(hourly_data)} rows from hourly_data for the current day")

        if not hourly_data:
            print("[INFO]: No hourly data available for the current day")
            return {"status": "error", "message": "No hourly data available for the current day"}

        # Step 2: Aggregate the data
        temperature = sum(row[2] for row in hourly_data) / len(hourly_data)
        relative_humidity = sum(row[3] for row in hourly_data) / len(hourly_data)
        rain = sum(row[4] for row in hourly_data)  # Total rainfall
        surface_pressure = sum(row[5] for row in hourly_data) / len(hourly_data)
        soil_moisture = sum(row[6] for row in hourly_data) / len(hourly_data)

        # Step 3: Insert aggregated data into daily_data
        print("[DEBUG]: Inserting aggregated data into daily_data")
        database_handler.update_dataset("daily_data", (
            temperature,
            relative_humidity,
            rain,
            surface_pressure,
            soil_moisture
        ))
        print("[DEBUG]: daily_data table updated successfully")

        # Close the database connection
        database_handler.close()
        return {"status": "success", "message": "daily_data table updated successfully"}
    except Exception as e:
        print("[ERROR]:", str(e))
        return {"status": "error", "message": str(e)}
    
def get_hourly_entry(n):
    """
    Fetch the last `n` entries from the hourly_data table.
    """
    database_handler = dbhandler.DatabaseHandler("../db-handler/dataset.db")
    last_entries = database_handler.get_last_entries("hourly_data", n)
    database_handler.close()
    data = []
    for entry in last_entries:
        data.append({
            "datetime": entry[1],  # Assuming datetime is the second column
            "temperature": entry[2],
            "relative_humidity": entry[3],
            "rain": entry[4],
            "surface_pressure": entry[5],
            "soil_moisture": entry[6]
        })
    return data


def get_hourly_prediction_entry(n):
    """
    Fetch the last `n` entries from the hourly_predictions table.
    """
    database_handler = dbhandler.DatabaseHandler("../db-handler/dataset.db")
    last_entries = database_handler.get_last_entries("hourly_predictions", n)
    database_handler.close()
    data = []
    for entry in last_entries:
        data.append({
            "datetime": entry[1],  # Assuming datetime is the second column
            "prediction_24": entry[2],
            "prediction_48": entry[3]
        })
    return data


# Add routes for the new methods
@app.route('/hourly')
@app.route('/hourly/<int:n>')
def hourly(n=1):
    hourly_data = get_hourly_entry(n)
    return jsonify(hourly_data)


@app.route('/hourly_prediction')
@app.route('/hourly_prediction/<int:n>')
def hourly_prediction(n=1):
    hourly_prediction_data = get_hourly_prediction_entry(n)
    return jsonify(hourly_prediction_data)    
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
@app.route('/aggregate_daily', methods=['POST'])
def aggregate_daily():
    result = aggregate_hourly_to_daily()
    return jsonify(result)

@app.route('/predict_daily', methods=['POST'])
def predict_daily():
    """
    Endpoint to predict daily flood risks and update the database.
    """
    try:
        # Create a new DatabaseHandler instance for this request
        database_handler = dbhandler.DatabaseHandler("../db-handler/dataset.db")

        # Call the prediction function from the predictor module
        prediction_24, prediction_48 = predictor.predict_flood()

        # Log predictions
        print("[INFO]: Daily Predictions - 24-hour:", prediction_24, "48-hour:", prediction_48)

        # Update the database with the predictions
        try:
            print("[DEBUG]: DatabaseHandler initialized")

            # Insert predictions into the daily_predictions table
            current_timestamp = int(time.time())  # Get current time as Unix timestamp
            database_handler.update_predictions("daily_predictions", (
                prediction_24,
                prediction_48
            ))
            print("[DEBUG]: daily_predictions table updated successfully")

        except Exception as db_error:
            print("[ERROR]: Failed to update the database:", str(db_error))
            return jsonify({"status": "error", "message": "Database update failed"}), 500

        finally:
            # Close the database connection
            database_handler.close()

        # Return predictions as a JSON response
        return jsonify({
            "status": "success",
            "predictions": {
                "24_hour": prediction_24,
                "48_hour": prediction_48
            }
        }), 200
    except Exception as e:
        print("[ERROR]: Failed to predict daily flood risks:", str(e))
        return jsonify({"status": "error", "message": str(e)}), 500
if __name__ == '__main__':
    
    app.run(debug=True)