```javascript
import React, { useState, useEffect } from 'react';
import axios from 'axios';

const CryptoPriceChart = ({ symbol }) => {
    const [price, setPrice] = useState(null);

    useEffect(() => {
        const fetchPrice = async () => {
            const response = await axios.get(`/api/v1/cryptocurrency/${symbol}`);
            setPrice(response.data.price_usd);
        };
        fetchPrice();
    }, [symbol]);

    return (
        <div>
            <h3>Cryptocurrency Price: {price ? `$${price.toFixed(2)}` : 'Loading...'}</h3>
        </div>
    );
};

export default CryptoPriceChart;
```