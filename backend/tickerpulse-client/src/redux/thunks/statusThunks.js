```javascript
import { fetchHealthStatus } from '../api';
import { setStatus } from '../reducers/statusReducer';

export const fetchHealthStatus = () => async (dispatch) => {
  try {
    const response = await fetchHealthStatusAPI();
    dispatch(setStatus(response));
  } catch (error) {
    console.error('Error fetching health status:', error);
  }
};

const fetchHealthStatusAPI = async () => {
  const response = await fetch('/api/health');
  if (!response.ok) {
    throw new Error('Failed to fetch health status');
  }
  return await response.json();
};
```