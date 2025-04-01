// API endpoints
const baseApiUrl = "http://127.0.0.1:5000";
const hourlyDataApiUrl = `${baseApiUrl}/hourly`;  // Hourly sensor data
const dailyDataApiUrl = `${baseApiUrl}/raw`;  // Daily sensor data for trends
const dailyPredApiUrl = `${baseApiUrl}/prediction`;  // Daily predictions for 24h and 48h forecasts
const hourlyPredApiUrl = `${baseApiUrl}/hourly_prediction`; // Hourly predictions for current risk

// Risk level mapping
const risk_level_map = {
    0: {
        label: "Low Risk",
        class: "risk-low"
    },
    1: {
        label: "Medium Risk",
        class: "risk-medium"
    },
    2: {
        label: "High Risk",
        class: "risk-high"
    }
};

// Chart variables
let forecastChart;
let currentChartType = 'all';
let currentDataSource = 'hourly'; // Default to hourly data
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
        // Show appropriate icon instead of numeric value
        if (risk.class === 'risk-low') {
            element.innerHTML = '<i class="material-icons">check_circle</i>';
        } else if (risk.class === 'risk-medium') {
            element.innerHTML = '<i class="material-icons">warning</i>';
        } else if (risk.class === 'risk-high') {
            element.innerHTML = '<i class="material-icons">error</i>';
        }
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
            
            // Add the new water flow and water depth fields
            if (document.getElementById("water-flow")) {
                document.getElementById("water-flow").textContent = formatValue(latest.water_flow, "m³/s");
            }
            
            if (document.getElementById("water-depth")) {
                document.getElementById("water-depth").textContent = formatValue(latest.water_depth, "m");
            }

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

// Fetch daily data for trend charts
async function fetchDailyData(n = 10) {
    try {
        showLoading();
        const response = await fetch(`${dailyDataApiUrl}/${n}`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        
        const data = await response.json();
        console.log("DAILY DATA: ", data);

        if (Array.isArray(data) && data.length > 0) {
            // Store data for chart
            chartData.daily = data;
            
            // Update chart with historical data
            updateChart(currentChartType);
        } else {
            console.error("No daily data received or invalid format");
        }

    } catch (error) {
        console.error("Error fetching daily data:", error);
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
            document.getElementById("24hr-forecast").textContent = risk_level_map[pred_24]?.label;
            document.getElementById("48hr-forecast").textContent = risk_level_map[pred_48]?.label;
            
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
            document.getElementById("current-risk").textContent = risk_level_map[current_risk]?.label;
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
    // Get data based on current data source selection
    const sourceData = currentDataSource === 'hourly' ? chartData.hourly : chartData.daily;
    
    // If no data, return
    if (!sourceData || sourceData.length === 0) return;
    
    currentChartType = chartType;
    const data = sourceData;
    
    // Prepare chart data
    const labels = data.map(entry => {
        return formatTimestamp(entry.datetime);
    });
    
    const temperatureData = data.map(entry => entry.temperature);
    const humidityData = data.map(entry => entry.relative_humidity);
    const rainData = data.map(entry => entry.rain);
    const soilData = data.map(entry => entry.soil_moisture);
    const pressureData = data.map(entry => entry.surface_pressure / 10); // Scale down for better visualization
    
    // Water flow and depth might only be available in hourly data
    const waterFlowData = currentDataSource === 'hourly' ? data.map(entry => entry.water_flow || 0) : [];
    const waterDepthData = currentDataSource === 'hourly' ? data.map(entry => entry.water_depth || 0) : [];

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
    
    // Add water metrics for hourly data
    if ((chartType === 'all' || chartType === 'water-metrics') && currentDataSource === 'hourly') {
        datasets.push({
            label: 'Water Flow (m³/s)',
            data: waterFlowData,
            borderColor: 'rgba(255, 206, 86, 1)',
            backgroundColor: 'rgba(255, 206, 86, 0.2)',
            borderWidth: 2,
            tension: 0.2,
            yAxisID: chartType === 'all' ? 'y1' : 'y'
        });
        
        datasets.push({
            label: 'Water Depth (m)',
            data: waterDepthData,
            borderColor: 'rgba(111, 66, 193, 1)',
            backgroundColor: 'rgba(111, 66, 193, 0.2)',
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
                text: getYAxisTitle(chartType),
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
                text: 'Rain (mm) / Soil Moisture (m³/m³) / Water Flow (m³/s) / Water Depth (m)'
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
                    text: `Sensor Data Trends (${currentDataSource === 'hourly' ? 'Hourly' : 'Daily'})`,
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

// Helper function to get Y-axis title based on chart type
function getYAxisTitle(chartType) {
    if (chartType === 'temp-humidity') {
        return 'Temperature (°C) / Humidity (%)';
    } else if (chartType === 'rain-soil') {
        return 'Rain (mm) / Soil Moisture (m³/m³)';
    } else if (chartType === 'water-metrics') {
        return 'Water Flow (m³/s) / Water Depth (m)';
    } else {
        return 'Temperature (°C) / Humidity (%) / Pressure (hPa/10)';
    }
}

// Toggle data source between hourly and daily
function toggleDataSource(source) {
    currentDataSource = source;
    if (source === 'hourly') {
        fetchHourlyData(parseInt(document.getElementById('data-range').value));
    } else {
        fetchDailyData(parseInt(document.getElementById('data-range').value));
    }
}

// Refresh all data
function refreshData() {
    showLoading();
    Promise.all([
        currentDataSource === 'hourly' 
            ? fetchHourlyData(parseInt(document.getElementById('data-range').value))
            : fetchDailyData(parseInt(document.getElementById('data-range').value)),
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
            if (currentDataSource === 'hourly') {
                fetchHourlyData(parseInt(e.target.value));
            } else {
                fetchDailyData(parseInt(e.target.value));
            }
        });
    }
    
    // Add event listener for data source toggle
    const dataToggle = document.getElementById('data-toggle');
    if (dataToggle) {
        dataToggle.addEventListener('change', (e) => {
            toggleDataSource(e.target.value);
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