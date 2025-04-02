import sys
import os
import time

# Ensure the correct path to import DatabaseHandler
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../db-handler')))

from dbhandler import DatabaseHandler  # Import your class

# Initialize database handler
db_name = "dataset.db"  # Change this to your actual database file
table_dataset = "daily_data"  # Replace with actual table name
table_predictions = "daily_predictions"  # Replace with actual table name

db_handler = DatabaseHandler(os.path.join(os.path.curdir, '..', 'db-handler', 'dataset.db'))

# Test update_dataset
data_sample = (25.3, 60.5, 0.0, 1013.2, 0.45)  # Example data: (temp, humidity, rain, pressure, soil moisture)
db_handler.update_dataset(table_dataset, data_sample)

# Test update_predictions
predictions_sample = (500.0, 520.0)  # Example predictions: (next 24h, next 48h)
db_handler.update_predictions(table_predictions, predictions_sample)

# Fetch and print last dataset entry
print("[INFO]: Last dataset entry:", db_handler.get_last_entries(table_dataset, 1))

# Fetch and print last prediction entry
print("[INFO]: Last prediction entry:", db_handler.get_last_entries(table_predictions, 1))
# Close connection
db_handler.close()
