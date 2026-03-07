```javascript
import React, { useEffect, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { fetchHealthStatus } from '../redux/thunks/statusThunks';
import { HealthStatus } from './HealthStatus';

const HealthDashboard = () => {
  const dispatch = useDispatch();
  const healthStatus = useSelector((state) => state.status.healthStatus);

  useEffect(() => {
    dispatch(fetchHealthStatus());
  }, [dispatch]);

  return (
    <div>
      <h2>Health Dashboard</h2>
      {healthStatus && <HealthStatus healthStatus={healthStatus} />}
    </div>
  );
};

export default HealthDashboard;
```