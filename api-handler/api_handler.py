from flask import Flask, request, jsonify
import sys
import os

# Add the db-handler directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../db-handler')))
import dbhandler
app = Flask(__name__)

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
    data = []
    for entry in last_entries:
        data.append({
            "datetime": entry[0],
            "prediction_24": entry[1],
            "prediction_48": entry[2]
        })
    return data
    
@app.route('/api/raw')
def index():
    raw_data = get_raw_entry(1)
    return jsonify(raw_data)

if __name__ == '__main__':
    app.run(debug=True)