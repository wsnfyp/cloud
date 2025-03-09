import dbhandler

database_handler = dbhandler.DatabaseHandler("dataset.db")
print(database_handler.get_last_entries("live_dataset", 5))

database_handler.update_predictions("predictions", (0.5, 0.7))
database_handler.close()