```javascript
import { FETCH_HEALTH_STATUS } from './types';

export const setStatus = (healthStatus) => ({
  type: FETCH_HEALTH_STATUS,
  payload: healthStatus
});
```