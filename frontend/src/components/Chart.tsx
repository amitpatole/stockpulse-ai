```typescript
import React, { useEffect, useState } from 'react';
import { useQuery } from '@apollo/client';
import { GET_CHART_DATA } from '../graphql/queries';

const Chart: React.FC = () => {
  const [chartData, setChartData] = useState<any[]>([]);

  useEffect(() => {
    const fetchChartData = async () => {
      try {
        const { data } = await fetch('/api/chart_data/AAPL');
        const chartData = await data;
        setChartData(chartData);
      } catch (error) {
        console.error('Error fetching chart data:', error);
      }
    };

    fetchChartData();
  }, []);

  return (
    <div>
      <h1>Chart Data</h1>
      <div>
        {chartData.map((data, index) => (
          <div key={index}>
            <h2>{data.Date}</h2>
            <p>Close: {data.Close}</p>
            {/* Add more data fields as needed */}
          </div>
        ))}
      </div>
    </div>
  );
};

export default Chart;
```