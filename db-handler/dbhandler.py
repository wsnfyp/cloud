import sqlite3
import os

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
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            print(f"[ERROR]: Can't fetch data: {e}")
            return None
        
    def update_predictions(self, table_name, predictions: tuple):
        try:
            self.execute_query(f"INSERT INTO {table_name} (name, age) VALUES (?, ?)", (name, age))
            print("[INFO]: Row added successfully.")
        except sqlite3.Error as e:
            print(f"[ERROR]: Can't add row: {e}")

    def close(self):
        if self.connection:
            self.connection.close()
            print("[INFO]: Database connection closed.")
        else:
            print("[ERROR]: No database connection to close.")