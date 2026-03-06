'use client';

import { useState, useEffect } from 'react';
import { PriceAlert, PaginationMeta } from '@/lib/types';
import { getPriceAlerts, deletePriceAlert } from '@/lib/api';
import { useToast } from '@/hooks/useToast';
import Button from '@/components/ui/Button';
import Dialog from '@/components/ui/Dialog';

interface PriceAlertsListProps {
  onSelectAlert?: (alert: PriceAlert) => void;
  onCreateClick?: () => void;
}

export function PriceAlertsList({ onSelectAlert, onCreateClick }: PriceAlertsListProps) {
  const [alerts, setAlerts] = useState<PriceAlert[]>([]);
  const [meta, setMeta] = useState<PaginationMeta | null>(null);
  const [loading, setLoading] = useState(true);
  const [ticker, setTicker] = useState('');
  const [activeOnly, setActiveOnly] = useState(false);
  const [deleteId, setDeleteId] = useState<number | null>(null);
  const { showToast } = useToast();

  useEffect(() => {
    loadAlerts();
  }, [ticker, activeOnly]);

  async function loadAlerts(offset = 0) {
    setLoading(true);
    try {
      const result = await getPriceAlerts(20, offset, ticker || undefined, activeOnly);
      setAlerts(result.alerts);
      setMeta(result.meta);
    } catch (error) {
      showToast('Failed to load alerts', 'error');
    } finally {
      setLoading(false);
    }
  }

  async function handleDelete() {
    if (!deleteId) return;
    try {
      await deletePriceAlert(deleteId);
      setDeleteId(null);
      showToast('Alert deleted', 'success');
      loadAlerts();
    } catch (error) {
      showToast('Failed to delete alert', 'error');
    }
  }

  const alertTypeColor = (type: string) => {
    switch (type) {
      case 'above':
        return 'bg-green-100 text-green-800';
      case 'below':
        return 'bg-red-100 text-red-800';
      case 'change_percent_up':
        return 'bg-blue-100 text-blue-800';
      case 'change_percent_down':
        return 'bg-orange-100 text-orange-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex gap-2">
        <input
          type="text"
          placeholder="Filter by ticker..."
          value={ticker}
          onChange={(e) => setTicker(e.target.value)}
          className="flex-1 px-3 py-2 border rounded-lg"
        />
        <label className="flex items-center gap-2">
          <input
            type="checkbox"
            checked={activeOnly}
            onChange={(e) => setActiveOnly(e.target.checked)}
          />
          Active only
        </label>
        <Button onClick={onCreateClick} variant="primary">
          + New Alert
        </Button>
      </div>

      <div className="space-y-2">
        {loading ? (
          <div className="text-center py-8 text-gray-500">Loading alerts...</div>
        ) : alerts.length === 0 ? (
          <div className="text-center py-8 text-gray-500">No price alerts configured</div>
        ) : (
          alerts.map((alert) => (
            <div
              key={alert.id}
              className="border rounded-lg p-3 hover:shadow-md cursor-pointer transition"
              onClick={() => onSelectAlert?.(alert)}
            >
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="font-semibold text-lg">{alert.ticker}</div>
                  <div className="flex gap-2 mt-1">
                    <span className={`px-2 py-1 rounded text-sm ${alertTypeColor(alert.alert_type)}`}>
                      {alert.alert_type.replace(/_/g, ' ')}
                    </span>
                    <span className="text-sm text-gray-600">${alert.threshold}</span>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <div className="text-right">
                    <div className="text-xs text-gray-500">
                      Triggered {alert.triggered_count} times
                    </div>
                    {alert.last_triggered_at && (
                      <div className="text-xs text-gray-500">
                        {new Date(alert.last_triggered_at).toLocaleDateString()}
                      </div>
                    )}
                  </div>
                  <input
                    type="checkbox"
                    checked={alert.is_active}
                    onChange={(e) => e.stopPropagation()}
                    className="w-4 h-4"
                    onClick={(e) => e.stopPropagation()}
                  />
                  <Button
                    onClick={(e) => {
                      e.stopPropagation();
                      setDeleteId(alert.id);
                    }}
                    variant="ghost"
                    size="sm"
                    className="text-red-600 hover:text-red-700"
                  >
                    Delete
                  </Button>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {meta && meta.total > 20 && (
        <div className="flex justify-center gap-2">
          <Button
            onClick={() => loadAlerts(Math.max(0, (meta.offset || 0) - 20))}
            disabled={!meta.has_previous}
            variant="ghost"
          >
            Previous
          </Button>
          <span className="py-2">Page {Math.floor((meta.offset || 0) / 20) + 1}</span>
          <Button
            onClick={() => loadAlerts((meta.offset || 0) + 20)}
            disabled={!meta.has_next}
            variant="ghost"
          >
            Next
          </Button>
        </div>
      )}

      <Dialog
        isOpen={deleteId !== null}
        onClose={() => setDeleteId(null)}
        title="Delete Alert"
        description="Are you sure you want to delete this price alert?"
        buttons={[
          {
            label: 'Cancel',
            onClick: () => setDeleteId(null),
            variant: 'secondary',
          },
          {
            label: 'Delete',
            onClick: handleDelete,
            variant: 'danger',
          },
        ]}
      />
    </div>
  );
}