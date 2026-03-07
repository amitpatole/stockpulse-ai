```javascript
import React, { useEffect, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { fetchCryptoData } from '../redux/actions/cryptoActions';
import CryptoOverview from './CryptoOverview';

const MarketOverview = () => {
    const dispatch = useDispatch();
    const { cryptocurrencies } = useSelector(state => state.crypto);

    useEffect(() => {
        dispatch(fetchCryptoData());
    }, [dispatch]);

    return (
        <div>
            <h1>Market Overview</h1>
            <CryptoOverview />
        </div>
    );
};

export default MarketOverview;
```