'use client';

import { useState } from 'react';
import { PriceAlert } from '@/lib/types';
import { updatePriceAlert, deletePriceAlert } from '@/lib/api';
import { useToast } from '@/hooks/useToast';
import Button from '@/components/ui/Button';

interface PriceAlertDetailPanelProps {
  alert: PriceAlert;
  onUpdate?: () => void;
  onDelete?: () => void;
}

export function PriceAlertDetailPanel({ alert, onUpdate, onDelete }: PriceAlertDetailPanelProps) {
  const [threshold, setThreshold] = useState(alert.threshold);
  const [isActive, setIsActive] = useState(alert.is_active);
  const [loading, setLoading] = useState(false);
  const [deleteConfirm, setDeleteConfirm] = useState(false);
  const { showToast } = useToast();

  async function handleUpdate() {
    setLoading(true);
    try {
      await updatePriceAlert(alert.id, threshold !== alert.threshold ? threshold : undefined, isActive !== alert.is_active ? isActive : undefined);
      showToast('Alert updated', 'success');
      onUpdate?.();
    } catch (error) {
      showToast('Failed to update alert', 'error');
    } finally {
      setLoading(false);
    }
  }

  async function handleDelete() {
    setLoading(true);
    try {
      await deletePriceAlert(alert.id);
      showToast('Alert deleted', 'success');
      onDelete?.();
    } catch (error) {
      showToast('Failed to delete alert', 'error');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="border rounded-lg p-6 space-y-4">
      <div>
        <h2 className="text-xl font-bold mb-2">{alert.ticker}</h2>
        <div className="text-sm text-gray-600">
          <p>Type: {alert.alert_type.replace(/_/g, ' ')}</p>
          <p>Created: {new Date(alert.created_at).toLocaleDateString()}</p>
        </div>
      </div>

      <div className="space-y-3">
        <div>
          <label className="block text-sm font-medium mb-1">Threshold</label>
          <input
            type="number"
            step="0.01"
            value={threshold}
            onChange={(e) => setThreshold(parseFloat(e.target.value) || 0)}
            className="w-full px-3 py-2 border rounded-lg"
          />
        </div>

        <div className="flex items-center gap-2">
          <input
            type="checkbox"
            id="isActive"
            checked={isActive}
            onChange={(e) => setIsActive(e.target.checked)}
          />
          <label htmlFor="isActive" className="text-sm font-medium">
            Alert Active
          </label>
        </div>

        <div className="text-sm text-gray-600">
          <p>Triggered: {alert.triggered_count} times</p>
          {alert.last_triggered_at && (
            <p>Last: {new Date(alert.last_triggered_at).toLocaleString()}</p>
          )}
        </div>
      </div>

      <div className="flex gap-2 pt-4">
        <Button
          onClick={handleUpdate}
          variant="primary"
          loading={loading}
          disabled={threshold === alert.threshold && isActive === alert.is_active}
        >
          Save Changes
        </Button>
        <Button
          onClick={() => setDeleteConfirm(true)}
          variant="danger"
          disabled={loading || deleteConfirm}
        >
          Delete
        </Button>
      </div>

      {deleteConfirm && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-3">
          <p className="text-sm text-red-800 mb-2">Are you sure? This cannot be undone.</p>
          <div className="flex gap-2">
            <Button
              onClick={handleDelete}
              variant="danger"
              size="sm"
              loading={loading}
            >
              Confirm Delete
            </Button>
            <Button
              onClick={() => setDeleteConfirm(false)}
              variant="secondary"
              size="sm"
              disabled={loading}
            >
              Cancel
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}