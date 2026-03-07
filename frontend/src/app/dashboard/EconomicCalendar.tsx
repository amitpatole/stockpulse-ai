```typescript
import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import { useQuery } from '@tanstack/react-query';
import { EconomicEventsAgent } from '../../backend/agents/economic_events';
import { AgentResult } from '../../backend/agents/base';

const EconomicCalendar: React.FC = () => {
  const router = useRouter();
  const [events, setEvents] = useState<AgentResult[]>([]);

  useEffect(() => {
    const fetchData = async () => {
      const result = await EconomicEventsAgent.run();
      setEvents([result]);
    };

    fetchData();
  }, []);

  return (
    <div>
      <h1>Economic Calendar</h1>
      <div>
        {events.map((event) => (
          <div key={event.agent_name}>
            <p>{event.output}</p>
          </div>
        ))}
      </div>
    </div>
  );
};

export default EconomicCalendar;
```