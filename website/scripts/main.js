// JSONPlaceholder API endpoint
const apiUrl = "https://jsonplaceholder.typicode.com/posts/1";

// Fetch data and update dashboard
async function fetchData() {
    try {
        const response = await fetch(apiUrl);
        const data = await response.json();

        // Update DOM with fetched data
        document.getElementById("24hr-forecast").textContent = `Forecast: ${data.title}`;
        document.getElementById("48hr-forecast").textContent = `Forecast: ${data.body.slice(0, 50)}...`;
        document.getElementById("water-level").textContent = `Level: ${data.id * 10}m`;
        document.getElementById("water-flow").textContent = `Flow: ${data.id * 5}m³/s`;
        document.getElementById("temperature").textContent = `Temp: ${data.userId}°C`;
        document.getElementById("humidity").textContent = `Humidity: ${data.id * 2}%`;
    } catch (error) {
        console.error("Error fetching data:", error);
    }
}

// Render Chart
const chartData = {
    labels: ['24hr', '48hr'],
    datasets: [{
        label: 'Flood Forecast',
        data: [24, 48], // Replace with actual data
        backgroundColor: ['rgba(75, 192, 192, 0.2)', 'rgba(153, 102, 255, 0.2)'],
        borderColor: ['rgba(75, 192, 192, 1)', 'rgba(153, 102, 255, 1)'],
        borderWidth: 1,
    }]
};

const chartConfig = {
    type: 'bar',
    data: chartData,
    options: {
        scales: {
            y: {
                beginAtZero: true
            }
        }
    }
};

const ctx = document.getElementById('forecast-chart').getContext('2d');
new Chart(ctx, chartConfig);

// Fetch data on page load
fetchData();