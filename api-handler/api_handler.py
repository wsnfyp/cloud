from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../db-handler')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../predictor')))
import predictor
import dbhandler
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
    data = request.json
    return jsonify({"status": "Data updated successfully"}), 200

if __name__ == '__main__':
    app.run(debug=True)
