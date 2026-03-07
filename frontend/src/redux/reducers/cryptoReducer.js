```javascript
import { FETCH_CRYPTO_DATA_SUCCESS, FETCH_CRYPTO_DATA_FAILURE } from '../actions/cryptoActions';

const initialState = {
    cryptocurrencies: [],
    error: null
};

const cryptoReducer = (state = initialState, action) => {
    switch (action.type) {
        case FETCH_CRYPTO_DATA_SUCCESS:
            return {
                ...state,
                cryptocurrencies: action.payload
            };
        case FETCH_CRYPTO_DATA_FAILURE:
            return {
                ...state,
                error: action.payload
            };
        default:
            return state;
    }
};

export default cryptoReducer;
```