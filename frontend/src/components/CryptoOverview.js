```javascript
import React, { useEffect, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { fetchCryptoData } from '../redux/actions/cryptoActions';

const CryptoOverview = () => {
    const dispatch = useDispatch();
    const { cryptocurrencies } = useSelector(state => state.crypto);

    useEffect(() => {
        dispatch(fetchCryptoData());
    }, [dispatch]);

    return (
        <div>
            <h2>Crypto Overview</h2>
            <ul>
                {cryptocurrencies.map(crypto => (
                    <li key={crypto.id}>
                        {crypto.name} ({crypto.symbol}): ${crypto.price_usd}
                    </li>
                ))}
            </ul>
        </div>
    );
};

export default CryptoOverview;
```