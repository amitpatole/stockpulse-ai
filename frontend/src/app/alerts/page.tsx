'use client';

import Header from '@/components/layout/Header';
import PriceAlertsPanel from '@/components/alerts/PriceAlertsPanel';

export default function AlertsPage() {
  return (
    <div className="flex flex-col">
      <Header title="Alerts" subtitle="Manage price alerts and notification sounds" />
      <div className="flex-1 p-6">
        <PriceAlertsPanel />
      </div>
    </div>
  );
}
