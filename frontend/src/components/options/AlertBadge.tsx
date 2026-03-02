```typescript
/**
 * TickerPulse AI - Alert Badge Component
 * Shows count of unread options flow alerts.
 */

import React from 'react';
import { useOptionsFlow } from '@/context/OptionsFlowContext';

export function AlertBadge() {
  const { unreadAlertCount } = useOptionsFlow();

  if (unreadAlertCount === 0) {
    return null;
  }

  return (
    <span className="absolute -top-2 -right-2 inline-flex items-center justify-center px-2 py-1 text-xs font-bold leading-none text-white transform translate-x-1/2 -translate-y-1/2 bg-red-600 rounded-full">
      {unreadAlertCount}
    </span>
  );
}
```