```typescript
'use client';

import { useState, useEffect } from 'react';
import { createPriceAlert, getStocks } from '@/lib/api';
import { useToast } from '@/hooks/useToast';
import Button from '@/components/ui/Button';
import Dialog from '@/components/ui/Dialog';

interface CreatePriceAlertDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

export function CreatePriceAlertDialog({ isOpen, onClose, onSuccess }: CreatePriceAlertDialogProps) {
  const [ticker, setTicker] = useState('');
  const [alertType, setAlertType] = useState<'above' | 'below' | 'change_percent_up' | 'change_percent_down'>(
    'above'
  );
  const [threshold, setThreshold] = useState('');
  const [stocks, setStocks] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const { showToast } = useToast();

  useEffect(() => {
    if (isOpen) {
      loadStocks();
    }
  }, [isOpen]);

  async function loadStocks() {
    try {
      const result = await getStocks(100, 0);
      setStocks(result.stocks || result);
    } catch (error) {
      console.error('Failed to load stocks:', error);
    }
  }

  function validate(): boolean {
    const newErrors: Record<string, string> = {};

    if (!ticker) newErrors.ticker = 'Ticker is required';
    if (!threshold) newErrors.threshold = 'Threshold is required';
    else if (parseFloat(threshold) <= 0) newErrors.threshold = 'Threshold must be positive';

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  }

  async function handleSubmit() {
    if (!validate()) return;

    setLoading(true);
    try {
      await createPriceAlert(ticker.toUpperCase(), alertType, parseFloat(threshold));
      showToast('Price alert created', 'success');
      onSuccess?.();
      handleClose();
    } catch (error: any) {
      showToast(error.message || 'Failed to create alert', 'error');
    } finally {
      setLoading(false);
    }
  }

  function handleClose() {
    setTicker('');
    setAlertType('above');
    setThreshold('');
    setErrors({});
    onClose();
  }

  return (
    <Dialog isOpen={isOpen} onClose={handleClose} title="Create Price Alert" hideClose>
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium mb-1">Stock Ticker</label>
          <select
            value={ticker}
            onChange={(e) => {
              setTicker(e.target.value);
              setErrors({ ...errors, ticker: '' });
            }}
            className={`w-full px-3 py-2 border rounded-lg ${errors.ticker ? 'border-red-500' : ''}`}
          >
            <option value="">Select a stock...</option>
            {stocks.map((stock) => (
              <option key={stock.id} value={stock.ticker}>
                {stock.ticker} - {stock.company_name}
              </option>
            ))}
          </select>
          {errors.ticker && <div className="text-sm text-red-600 mt-1">{errors.ticker}</div>}
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Alert Type</label>
          <div className="space-y-2">
            {(['above', 'below', 'change_percent_up', 'change_percent_down'] as const).map((type) => (
              <label key={type} className="flex items-center gap-2">
                <input
                  type="radio"
                  name="alertType"
                  value={type}
                  checked={alertType === type}
                  onChange={(e) => setAlertType(e.target.value as any)}
                />
                <span>{type.replace(/_/g, ' ')}</span>
              </label>
            ))}
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">
            {alertType.startsWith('change_percent') ? 'Percentage Change (%)' : 'Price Threshold ($)'}
          </label>
          <input
            type="number"
            step="0.01"
            min="0"
            value={threshold}
            onChange={(e) => {
              setThreshold(e.target.value);
              setErrors({ ...errors, threshold: '' });
            }}
            placeholder="e.g., 150.00"
            className={`w-full px-3 py-2 border rounded-lg ${errors.threshold ? 'border-red-500' : ''}`}
          />
          {errors.threshold && <div className="text-sm text-red-600 mt-1">{errors.threshold}</div>}
        </div>

        <div className="flex justify-end gap-2">
          <Button onClick={handleClose} variant="secondary" disabled={loading}>
            Cancel
          </Button>
          <Button onClick={handleSubmit} variant="primary" loading={loading}>
            Create Alert
          </Button>
        </div>
      </div>
    </Dialog>
  );
}
```