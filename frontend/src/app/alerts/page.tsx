```typescript
'use client';

import { useState } from 'react';
import { PriceAlert } from '@/lib/types';
import { PriceAlertsList } from '@/components/PriceAlertsList';
import { CreatePriceAlertDialog } from '@/components/CreatePriceAlertDialog';
import { PriceAlertDetailPanel } from '@/components/PriceAlertDetailPanel';

export default function AlertsPage() {
  const [selectedAlert, setSelectedAlert] = useState<PriceAlert | null>(null);
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);

  return (
    <div className="max-w-7xl mx-auto py-8 px-4">
      <h1 className="text-3xl font-bold mb-8">Price Alerts</h1>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2">
          <PriceAlertsList
            key={refreshKey}
            onSelectAlert={setSelectedAlert}
            onCreateClick={() => setIsCreateDialogOpen(true)}
          />
        </div>

        {selectedAlert && (
          <div className="lg:col-span-1">
            <PriceAlertDetailPanel
              alert={selectedAlert}
              onUpdate={() => {
                setRefreshKey((k) => k + 1);
                setSelectedAlert(null);
              }}
              onDelete={() => {
                setRefreshKey((k) => k + 1);
                setSelectedAlert(null);
              }}
            />
          </div>
        )}
      </div>

      <CreatePriceAlertDialog
        isOpen={isCreateDialogOpen}
        onClose={() => setIsCreateDialogOpen(false)}
        onSuccess={() => setRefreshKey((k) => k + 1)}
      />
    </div>
  );
}
```