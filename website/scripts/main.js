// JSONPlaceholder API endpoint
const baseApiUrl = "http://98.70.76.114/api";
const dataApiUrl = `${baseApiUrl}/raw/10`;  // Default to 10 entries
const predApiUrl = `${baseApiUrl}/prediction`;

// Chart variables
let forecastChart;

// Fetch data and update dashboard
async function fetchData(n = 10) {
    try {
        const response = await fetch(`${baseApiUrl}/raw/${n}`);
        const data = await response.json();
        console.log("RAW DATA: ", data);

        if (Array.isArray(data) && data.length > 0) {
            // Update dashboard with latest entry
            const latest = data[data.length - 1];
            document.getElementById("soil-moisture").textContent = `Soil Moisture: ${latest.soil_moisture}m`;
            document.getElementById("rain").textContent = `Rain: ${latest.rain}mm`;
            document.getElementById("temperature").textContent = `Temp: ${latest.temperature}°C`;
            document.getElementById("humidity").textContent = `Humidity: ${latest.relative_humidity}%`;
            document.getElementById("surface-pressure").textContent = `Surface Pressure: ${latest.surface_pressure}hPa`;

            // Update chart with historical data
            updateChart(data);
        } else {
            console.error("No data received or invalid format");
        }

    } catch (error) {
        console.error("Error fetching data:", error);
    }
}

async function fetchPrediction() {
    try {
        const response = await fetch(predApiUrl);
        const data = await response.json();
        const prediction_level_map = new Map([
            [0, "Low Risk (Below 50%)"],
            [1, "Medium Risk (75% - 90%)"],
            [2, "High Risk (Above 90%))"]
        ]);
        
        console.log("PREDICTION: ", data);
        const pred_24 = data.prediction_24;
        const pred_48 = data.prediction_48;
        
        document.getElementById("24hr-forecast").textContent = `Forecast: ${prediction_level_map.get(pred_24)}`;
        document.getElementById("48hr-forecast").textContent = `Forecast: ${prediction_level_map.get(pred_48)}`;
        
    } catch (error) {
        console.error("Error fetching prediction data:", error);
    }
}

function updateChart(data) {
    // Prepare chart data
    const labels = data.map(entry => {
        const date = new Date(entry.datetime);
        return date.toLocaleTimeString(); // Or format as needed
    });
    
    const temperatureData = data.map(entry => entry.temperature);
    const humidityData = data.map(entry => entry.relative_humidity);
    const rainData = data.map(entry => entry.rain);
    const soilData = data.map(entry => entry.soil_moisture);

    // Destroy previous chart if it exists
    if (forecastChart) {
        forecastChart.destroy();
    }

    const ctx = document.getElementById('forecast-chart').getContext('2d');
    
    forecastChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Temperature (°C)',
                    data: temperatureData,
                    borderColor: 'rgba(255, 99, 132, 1)',
                    backgroundColor: 'rgba(255, 99, 132, 0.2)',
                    borderWidth: 1,
                    yAxisID: 'y'
                },
                {
                    label: 'Humidity (%)',
                    data: humidityData,
                    borderColor: 'rgba(54, 162, 235, 1)',
                    backgroundColor: 'rgba(54, 162, 235, 0.2)',
                    borderWidth: 1,
                    yAxisID: 'y'
                },
                {
                    label: 'Rain (mm)',
                    data: rainData,
                    borderColor: 'rgba(75, 192, 192, 1)',
                    backgroundColor: 'rgba(75, 192, 192, 0.2)',
                    borderWidth: 1,
                    yAxisID: 'y1'
                },
                {
                    label: 'Soil Moisture (m)',
                    data: soilData,
                    borderColor: 'rgba(153, 102, 255, 1)',
                    backgroundColor: 'rgba(153, 102, 255, 0.2)',
                    borderWidth: 1,
                    yAxisID: 'y1'
                }
            ]
        },
        options: {
            responsive: true,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            scales: {
                y: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    title: {
                        display: true,
                        text: 'Temperature/Humidity'
                    }
                },
                y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    title: {
                        display: true,
                        text: 'Rain/Soil Moisture'
                    },
                    grid: {
                        drawOnChartArea: false,
                    }
                }
            }
        }
    });
}

// Initialize the page
function init() {
    // Add event listener for data range selector
    const rangeSelector = document.getElementById('data-range');
    if (rangeSelector) {
        rangeSelector.addEventListener('change', (e) => {
            fetchData(parseInt(e.target.value));
        });
    }

    // Initial data fetch
    fetchData();
    fetchPrediction();
}

// Start when DOM is loaded
document.addEventListener('DOMContentLoaded', init);