```javascript
import { useEffect, useState } from 'react';
import axios from 'axios';

function HealthDashboard() {
    const [healthData, setHealthData] = useState(null);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const response = await axios.get('/api/health');
                setHealthData(response.data);
            } catch (error) {
                console.error('Error fetching health data:', error);
            }
        };

        fetchData();
    }, []);

    return (
        <div>
            <h1>Health Dashboard</h1>
            {healthData ? (
                <div>
                    <p>Status: {healthData.status}</p>
                    <p>Latency: {healthData.latency_ms} ms</p>
                    <p>Error Rate: {healthData.error_rate}%</p>
                </div>
            ) : (
                <p>Loading...</p>
            )}
        </div>
    );
}

export default HealthDashboard;
```