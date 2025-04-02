import requests
from datetime import datetime, timedelta,timezone
import numpy as np
def get_previous_hour_weather():
    # Open-Meteo API URL
    url = "https://api.open-meteo.com/v1/forecast?latitude=11.3046&longitude=75.8777&hourly=rain,soil_moisture_0_to_1cm&forecast_days=1"
    
    try:
        # Make the API request
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for bad status codes
        data = response.json()

        # Extract hourly data
        times = data["hourly"]["time"]
        rain = data["hourly"]["rain"]
        soil_moisture = data["hourly"]["soil_moisture_0_to_1cm"]

        # Get the current UTC time and adjust to IST (UTC+5:30)
        current_time = datetime.now(timezone.utc) + timedelta(hours=5, minutes=30)
        previous_hour = current_time - timedelta(hours=1)
        previous_hour_str = previous_hour.strftime("%Y-%m-%dT%H:00")

        # Find the index of the previous hour in the API response
        if previous_hour_str in times:
            index = times.index(previous_hour_str)
            previous_rain = rain[index]
            previous_soil_moisture = soil_moisture[index]
        else:
            raise ValueError(f"Previous hour data not found for {previous_hour_str}")

        return previous_rain, previous_soil_moisture

    except Exception as e:
        print(f"[ERROR]: Failed to fetch previous hour weather data: {e}")
        return 0.0, 0.0  # Default values in case of an error

def get_previous_day_weather():
    url = "https://api.open-meteo.com/v1/forecast?latitude=11.3046&longitude=75.8777&hourly=rain,soil_moisture_0_to_1cm&past_days=1&forecast_days=1"
    
    response = requests.get(url)
    data = response.json()
    
    # Extract hourly values
    times = data["hourly"]["time"]
    rain = data["hourly"]["rain"][:24]  # First 24 hours (previous day)
    soil_moisture = data["hourly"]["soil_moisture_0_to_1cm"][:24]

    # Compute daily values
    total_rainfall = sum(rain)
    avg_soil_moisture = np.mean(soil_moisture)

    return total_rainfall, avg_soil_moisture


if __name__ == "__main__":
    rain, moisture = get_previous_day_weather()
    print(f"Previous day's total rainfall: {rain} mm")
    print(f"Previous day's average soil moisture: {moisture} m³/m³")
    rain, moisture = get_previous_hour_weather()
    print(f"Previous hour's rainfall: {rain} mm")
    print(f"Previous hour's soil moisture: {moisture} m³/m³")