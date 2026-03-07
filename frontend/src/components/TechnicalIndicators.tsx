```typescript
import React, { useEffect, useState } from 'react';
import { useQuery } from '@apollo/client';
import { GET_TECHNICAL_INDICATORS } from '../graphql/queries';

const TechnicalIndicators: React.FC = () => {
  const [indicators, setIndicators] = useState<any[]>([]);

  useEffect(() => {
    const fetchTechnicalIndicators = async () => {
      try {
        const { data } = await fetch('/api/technical_indicators/AAPL');
        const indicators = await data;
        setIndicators(indicators);
      } catch (error) {
        console.error('Error fetching technical indicators:', error);
      }
    };

    fetchTechnicalIndicators();
  }, []);

  return (
    <div>
      <h1>Technical Indicators</h1>
      <table>
        <thead>
          <tr>
            <th>Date</th>
            <th>Close</th>
            <th>RSI</th>
            <th>MACD</th>
            <th>Signal</th>
            <th>Upper Band</th>
            <th>Lower Band</th>
            <th>SMA</th>
            <th>EMA</th>
          </tr>
        </thead>
        <tbody>
          {indicators.map((indicator, index) => (
            <tr key={index}>
              <td>{indicator.Date}</td>
              <td>{indicator.Close}</td>
              <td>{indicator.RSI}</td>
              <td>{indicator.MACD}</td>
              <td>{indicator.Signal}</td>
              <td>{indicator.Upper}</td>
              <td>{indicator.Lower}</td>
              <td>{indicator.SMA}</td>
              <td>{indicator.EMA}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default TechnicalIndicators;
```