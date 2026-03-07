```javascript
import axios from 'axios';

export const fetchCryptoData = () => async (dispatch) => {
    try {
        const response = await axios.get('/api/v1/cryptocurrencies');
        dispatch({
            type: 'FETCH_CRYPTO_DATA_SUCCESS',
            payload: response.data
        });
    } catch (error) {
        dispatch({
            type: 'FETCH_CRYPTO_DATA_FAILURE',
            payload: error
        });
    }
};
```