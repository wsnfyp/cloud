// API endpoints
const baseApiUrl = "http://98.70.76.114/api";
const hourlyDataApiUrl = `${baseApiUrl}/hourly`;  // Hourly sensor data
const dailyPredApiUrl = `${baseApiUrl}/prediction`;  // Daily predictions for 24h and 48h forecasts
const hourlyPredApiUrl = `${baseApiUrl}/hourly_prediction`; // Hourly predictions for current risk

// Risk level mapping
const risk_level_map = {
    0: {
        label: "Low Risk",
        description: "Below 50% probability of flooding",
        class: "risk-low"
    },
    1: {
        label: "Medium Risk",
        description: "75% - 90% probability of flooding",
        class: "risk-medium"
    },
    2: {
        label: "High Risk",
        description: "Above 90% probability of flooding",
        class: "risk-high"
    }
};

// Chart variables
let forecastChart;
let currentChartType = 'all';
let chartData = {};

// Show loading overlay
function showLoading() {
    document.getElementById('loading-overlay').classList.remove('hidden');
}

// Hide loading overlay
function hideLoading() {
    document.getElementById('loading-overlay').classList.add('hidden');
}

// Format timestamp
function formatTimestamp(timestamp) {
    // Check if timestamp is a number (Unix timestamp)
    if (!isNaN(timestamp)) {
        // Convert seconds to milliseconds
        return new Date(timestamp * 1000).toLocaleString();
    }
    
    // Already a date string
    return new Date(timestamp).toLocaleString();
}

// Update last updated time
function updateLastUpdated() {
    const now = new Date();
    document.getElementById('last-updated').textContent = `Last updated: ${now.toLocaleString()}`;
}

// Format data value with unit
function formatValue(value, unit, precision = 1) {
    if (value === undefined || value === null) return "N/A";
    return `${parseFloat(value).toFixed(precision)}${unit}`;
}

// Setup risk indicator
function setupRiskIndicator(elementId, riskLevel) {
    const element = document.getElementById(elementId);
    if (!element) return;
    
    // Clear previous classes
    element.className = 'risk-indicator';
    
    if (riskLevel === "Insufficient Data" || riskLevel === undefined) {
        element.classList.add('risk-medium');
        element.textContent = "?";
        return;
    }
    
    // Add appropriate class and text
    const risk = risk_level_map[riskLevel];
    if (risk) {
        element.classList.add(risk.class);
        element.textContent = riskLevel;
    }
}

// Fetch hourly sensor data and update dashboard
async function fetchHourlyData(n = 10) {
    try {
        showLoading();
        const response = await fetch(`${hourlyDataApiUrl}/${n}`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        
        const data = await response.json();
        console.log("HOURLY DATA: ", data);

        if (Array.isArray(data) && data.length > 0) {
            // Store data for chart
            chartData.hourly = data;
            
            // Update dashboard with latest entry
            const latest = data[data.length - 1];
            document.getElementById("soil-moisture").textContent = formatValue(latest.soil_moisture, "m³/m³");
            document.getElementById("rain").textContent = formatValue(latest.rain, "mm");
            document.getElementById("temperature").textContent = formatValue(latest.temperature, "°C");
            document.getElementById("humidity").textContent = formatValue(latest.relative_humidity, "%");
            document.getElementById("surface-pressure").textContent = formatValue(latest.surface_pressure, "hPa");

            // Update chart with historical data
            updateChart(currentChartType);
        } else {
            console.error("No hourly data received or invalid format");
        }

    } catch (error) {
        console.error("Error fetching hourly data:", error);
    } finally {
        hideLoading();
    }
}

// Fetch daily predictions for 24h and 48h forecasts
async function fetchDailyPrediction() {
    try {
        showLoading();
        const response = await fetch(dailyPredApiUrl);
        
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        
        const data = await response.json();
        console.log("DAILY PREDICTION: ", data);
        
        if (Array.isArray(data) && data.length > 0) {
            // Get the most recent prediction
            const latestPrediction = data[data.length - 1];
            const pred_24 = latestPrediction.prediction_24;
            const pred_48 = latestPrediction.prediction_48;
            
            // Update forecast text
            document.getElementById("24hr-forecast").textContent = risk_level_map[pred_24]?.label + " - " + risk_level_map[pred_24]?.description;
            document.getElementById("48hr-forecast").textContent = risk_level_map[pred_48]?.label + " - " + risk_level_map[pred_48]?.description;
            
            // Update risk indicators
            setupRiskIndicator("24hr-risk-indicator", pred_24);
            setupRiskIndicator("48hr-risk-indicator", pred_48);
        } else {
            console.error("No daily prediction data received or invalid format");
        }
    } catch (error) {
        console.error("Error fetching daily prediction data:", error);
    } finally {
        hideLoading();
    }
}

// Fetch hourly prediction for current risk
async function fetchHourlyPrediction() {
    try {
        showLoading();
        const response = await fetch(hourlyPredApiUrl);
        
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        
        const data = await response.json();
        console.log("HOURLY PREDICTION: ", data);
        
        if (Array.isArray(data) && data.length > 0) {
            // Get the most recent prediction
            const latestPrediction = data[data.length - 1];
            const current_risk = latestPrediction.prediction_24; // Using the 24h prediction as current risk
            
            // Update current risk text and indicator
            document.getElementById("current-risk").textContent = risk_level_map[current_risk]?.label + " - " + risk_level_map[current_risk]?.description;
            setupRiskIndicator("current-risk-indicator", current_risk);
        } else {
            console.error("No hourly prediction data received or invalid format");
        }
    } catch (error) {
        console.error("Error fetching hourly prediction data:", error);
    } finally {
        hideLoading();
    }
}

function updateChart(chartType = 'all') {
    // If no data, return
    if (!chartData.hourly || chartData.hourly.length === 0) return;
    
    currentChartType = chartType;
    const data = chartData.hourly;
    
    // Prepare chart data
    const labels = data.map(entry => {
        return formatTimestamp(entry.datetime);
    });
    
    const temperatureData = data.map(entry => entry.temperature);
    const humidityData = data.map(entry => entry.relative_humidity);
    const rainData = data.map(entry => entry.rain);
    const soilData = data.map(entry => entry.soil_moisture);
    const pressureData = data.map(entry => entry.surface_pressure / 10); // Scale down for better visualization

    // Destroy previous chart if it exists
    if (forecastChart) {
        forecastChart.destroy();
    }

    const ctx = document.getElementById('forecast-chart').getContext('2d');
    const datasets = [];
    
    // Configure datasets based on chart type
    if (chartType === 'all' || chartType === 'temp-humidity') {
        datasets.push({
            label: 'Temperature (°C)',
            data: temperatureData,
            borderColor: 'rgba(255, 99, 132, 1)',
            backgroundColor: 'rgba(255, 99, 132, 0.2)',
            borderWidth: 2,
            tension: 0.2,
            yAxisID: 'y'
        });
        
        datasets.push({
            label: 'Humidity (%)',
            data: humidityData,
            borderColor: 'rgba(54, 162, 235, 1)',
            backgroundColor: 'rgba(54, 162, 235, 0.2)',
            borderWidth: 2,
            tension: 0.2,
            yAxisID: 'y'
        });
    }
    
    if (chartType === 'all') {
        datasets.push({
            label: 'Pressure (hPa/10)',
            data: pressureData,
            borderColor: 'rgba(255, 159, 64, 1)',
            backgroundColor: 'rgba(255, 159, 64, 0.2)',
            borderWidth: 2,
            tension: 0.2,
            yAxisID: 'y'
        });
    }
    
    if (chartType === 'all' || chartType === 'rain-soil') {
        datasets.push({
            label: 'Rain (mm)',
            data: rainData,
            borderColor: 'rgba(75, 192, 192, 1)',
            backgroundColor: 'rgba(75, 192, 192, 0.2)',
            borderWidth: 2,
            tension: 0.2,
            yAxisID: chartType === 'all' ? 'y1' : 'y'
        });
        
        datasets.push({
            label: 'Soil Moisture (m³/m³)',
            data: soilData,
            borderColor: 'rgba(153, 102, 255, 1)',
            backgroundColor: 'rgba(153, 102, 255, 0.2)',
            borderWidth: 2,
            tension: 0.2,
            yAxisID: chartType === 'all' ? 'y1' : 'y'
        });
    }
    
    // Chart configuration
    const scales = {
        x: {
            ticks: {
                maxRotation: 45,
                minRotation: 45
            }
        },
        y: {
            type: 'linear',
            display: true,
            position: 'left',
            title: {
                display: true,
                text: chartType === 'rain-soil' 
                    ? 'Rain (mm) / Soil Moisture (m³/m³)' 
                    : 'Temperature (°C) / Humidity (%) / Pressure (hPa/10)'
            },
            grid: {
                color: 'rgba(0, 0, 0, 0.1)'
            }
        }
    };
    
    // Add second y-axis for all metrics view
    if (chartType === 'all') {
        scales.y1 = {
            type: 'linear',
            display: true,
            position: 'right',
            title: {
                display: true,
                text: 'Rain (mm) / Soil Moisture (m³/m³)'
            },
            grid: {
                drawOnChartArea: false,
            }
        };
    }
    
    forecastChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: datasets
        },
        options: {
            responsive: true,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            plugins: {
                title: {
                    display: true,
                    text: 'Sensor Data Trends',
                    font: {
                        size: 16
                    }
                },
                tooltip: {
                    callbacks: {
                        title: function(tooltipItems) {
                            return formatTimestamp(data[tooltipItems[0].dataIndex].datetime);
                        }
                    }
                }
            },
            scales: scales
        }
    });
}

// Refresh all data
function refreshData() {
    showLoading();
    Promise.all([
        fetchHourlyData(parseInt(document.getElementById('data-range').value)),
        fetchDailyPrediction(),
        fetchHourlyPrediction()
    ]).then(() => {
        updateLastUpdated();
        hideLoading();
    }).catch(error => {
        console.error("Error refreshing data:", error);
        hideLoading();
    });
}

// Initialize the page
function init() {
    // Add event listener for refresh button
    const refreshBtn = document.getElementById('refresh-btn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', refreshData);
    }

    // Add event listener for data range selector
    const rangeSelector = document.getElementById('data-range');
    if (rangeSelector) {
        rangeSelector.addEventListener('change', (e) => {
            fetchHourlyData(parseInt(e.target.value));
        });
    }
    
    // Add event listeners for chart tabs
    const chartTabs = document.querySelectorAll('.chart-tab');
    chartTabs.forEach(tab => {
        tab.addEventListener('click', (e) => {
            // Remove active class from all tabs
            chartTabs.forEach(t => t.classList.remove('active'));
            // Add active class to clicked tab
            e.target.classList.add('active');
            // Update chart
            updateChart(e.target.dataset.chart);
        });
    });

    // Initial data fetch
    refreshData();
    
    // Set up auto-refresh every 5 minutes
    setInterval(refreshData, 5 * 60 * 1000);
}

// Start when DOM is loaded
document.addEventListener('DOMContentLoaded', init);