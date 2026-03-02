```typescript
'use client';

import { useContext } from 'react';
import { TourContext, TourContextType } from '@/context/TourContext';

export function useTour(): TourContextType {
  const context = useContext(TourContext);
  if (!context) {
    throw new Error('useTour must be used within TourProvider');
  }
  return context;
}
```