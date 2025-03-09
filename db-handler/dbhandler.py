import sqlite3
import os
import time

class DatabaseHandler:
    def __init__(self, db_name):
        if not (os.path.exists(db_name)):
            print(f"[ERROR]: Database {db_name} does not exist.")
        
        self.connection = sqlite3.connect(db_name)
        self.cursor = self.connection.cursor()

    def execute_query(self, query, params=()):
        try:
            self.cursor.execute(query, params)
            self.connection.commit()
        except sqlite3.Error as e:
            print(f"[ERROR]: Can't execute query: {e}")

    def get_last_entries(self, table_name, n=1):
        try:
            self.cursor.execute(f"SELECT * FROM {table_name} ORDER BY datetime DESC LIMIT {n}")
            return self.cursor.fetchall()[::-1]
        except sqlite3.Error as e:
            print(f"[ERROR]: Can't fetch data: {e}")
            return None
    
    def update_dataset(self, table_name, data: tuple):
        try:
            print("[INFO]: Updating Dataset...")
            self.execute_query(f"INSERT INTO {table_name} (datetime, temperature, relative_humidity, rain, surface_pressure, soil_moisture) VALUES (?, ?, ?, ?, ?, ?)", 
                               (int(time.time()), data[0], data[1], data[2], data[3], data[4]))
        except sqlite3.Error as e:
            print(f"[ERROR]: Can't add row: {e}")
        
    def update_predictions(self, table_name, predictions: tuple):
        try:
            print("[INFO]: Updating Predictions...")
            self.execute_query(f"INSERT INTO {table_name} (datetime, prediction_24, prediction_48) VALUES (?, ?, ?)", 
                               (int(time.time()), predictions[0], predictions[1]))
        except sqlite3.Error as e:
            print(f"[ERROR]: Can't add row: {e}")

    def close(self):
        if self.connection:
            self.connection.close()
            print("[INFO]: Database connection closed.")
        else:
            print("[ERROR]: No database connection to close.")
    
    def __del__(self):
        self.close()