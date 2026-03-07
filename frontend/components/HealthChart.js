```javascript
import React, { useEffect, useState } from 'react';
import { Line } from 'react-chartjs-2';
import axios from 'axios';

const HealthChart = () => {
    const [data, setData] = useState({});

    useEffect(() => {
        const fetchData = async () => {
            try {
                const response = await axios.get('/api/health');
                setData(response.data);
            } catch (error) {
                console.error('Error fetching health data:', error);
            }
        };

        fetchData();
    }, []);

    const options = {
        scales: {
            xAxes: [{ type: 'time', time: { unit: 'second' } }],
            yAxes: [{ ticks: { beginAtZero: true } }]
        }
    };

    const chartData = {
        labels: [data.timestamp],
        datasets: [
            {
                label: 'Latency (ms)',
                data: [data.latency_ms],
                fill: false,
                borderColor: 'rgb(75, 192, 192)',
                tension: 0.1
            },
            {
                label: 'Error Rate (%)',
                data: [data.error_rate],
                fill: false,
                borderColor: 'rgb(153, 102, 255)',
                tension: 0.1
            }
        ]
    };

    return (
        <div>
            <h1>Health Dashboard</h1>
            <Line data={chartData} options={options} />
        </div>
    );
};

export default HealthChart;
```