import requests
import numpy as np

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

# Example usage
if __name__ == "__main__":
    rain, moisture = get_previous_day_weather()
    print(f"Previous day's total rainfall: {rain} mm")
    print(f"Previous day's average soil moisture: {moisture} m³/m³")
