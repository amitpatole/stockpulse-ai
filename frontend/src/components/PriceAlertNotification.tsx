```typescript
'use client';

import { useEffect } from 'react';
import { PriceAlertTriggerEvent } from '@/lib/types';
import { useDesktopNotification } from '@/hooks/useDesktopNotification';

interface PriceAlertNotificationProps {
  alert: PriceAlertTriggerEvent;
  onDismiss: () => void;
}

export function PriceAlertNotification({ alert, onDismiss }: PriceAlertNotificationProps) {
  const { sendNotification, requestPermission } = useDesktopNotification();

  useEffect(() => {
    const handleNotification = async () => {
      await requestPermission();
      await sendNotification({
        title: `Price Alert: ${alert.ticker}`,
        body: `${alert.ticker} is trading at $${alert.current_price.toFixed(2)} (Alert: ${alert.alert_type} $${alert.threshold.toFixed(2)})`,
        tag: `price-alert-${alert.alert_id}`,
        requireInteraction: true,
      });

      setTimeout(onDismiss, 5000);
    };

    handleNotification();
  }, [alert, requestPermission, sendNotification, onDismiss]);

  return (
    <div className="fixed bottom-4 right-4 bg-white rounded-lg shadow-lg p-4 max-w-sm border-l-4 border-blue-500 animate-slideIn">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h3 className="font-semibold text-lg text-gray-900">{alert.ticker}</h3>
          <p className="text-sm text-gray-600 mt-1">
            Trading at <span className="font-semibold">${alert.current_price.toFixed(2)}</span>
          </p>
          <p className="text-sm text-gray-600">
            Alert: {alert.alert_type} {alert.threshold.toFixed(2)}
          </p>
        </div>
        <button
          onClick={onDismiss}
          className="text-gray-400 hover:text-gray-600 text-lg leading-none"
        >
          ✕
        </button>
      </div>
    </div>
  );
}
```