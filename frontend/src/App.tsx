```typescript
import React from 'react';
import TechnicalIndicators from './components/TechnicalIndicators';
import Chart from './components/Chart';

const App: React.FC = () => {
  return (
    <div>
      <h1>TickerPulse Dashboard</h1>
      <TechnicalIndicators />
      <Chart />
    </div>
  );
};

export default App;
```