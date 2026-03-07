```javascript
import { FETCH_HEALTH_STATUS } from '../actions/statusActions';

const initialState = {
  healthStatus: null
};

const statusReducer = (state = initialState, action) => {
  switch (action.type) {
    case FETCH_HEALTH_STATUS:
      return { ...state, healthStatus: action.payload };
    default:
      return state;
  }
};

export default statusReducer;
```