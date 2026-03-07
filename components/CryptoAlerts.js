```javascript
import React, { useState, useEffect } from 'react';
import axios from 'axios';

const CryptoAlerts = ({ symbol }) => {
    const [alerts, setAlerts] = useState([]);

    useEffect(() => {
        const fetchAlerts = async () => {
            const response = await axios.get(`/api/v1/cryptocurrency/${symbol}/alerts`);
            setAlerts(response.data);
        };
        fetchAlerts();
    }, [symbol]);

    return (
        <div>
            <h3>Crypto Alerts:</h3>
            <ul>
                {alerts.map(alert => (
                    <li key={alert.id}>{alert.message}</li>
                ))}
            </ul>
        </div>
    );
};

export default CryptoAlerts;
```