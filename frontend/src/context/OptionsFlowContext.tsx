```typescript
/**
 * TickerPulse AI - Options Flow Context
 * Manages state for options flow data and subscriptions across the app.
 */

import React, { createContext, useContext, useState, useCallback } from 'react';

export interface OptionFlow {
  id: number;
  ticker: string;
  contract: string;
  option_type: string;
  strike: number;
  expiration: string;
  volume: number;
  open_interest: number;
  bid_ask_spread: number;
  iv_percentile: number;
  flow_type: string;
  anomaly_score: number;
  created_at: string;
  is_alert: boolean;
  user_note?: string;
}

export interface AlertSubscription {
  id: number;
  ticker?: string;
  flow_type?: string;
  min_anomaly_score: number;
  is_active: boolean;
  created_at: string;
}

interface OptionsFlowContextType {
  flows: OptionFlow[];
  subscriptions: AlertSubscription[];
  unreadAlertCount: number;
  isLoading: boolean;
  error?: string;
  addFlow: (flow: OptionFlow) => void;
  updateFlow: (id: number, updates: Partial<OptionFlow>) => void;
  removeFlow: (id: number) => void;
  clearFlows: () => void;
  setFlows: (flows: OptionFlow[]) => void;
  addSubscription: (subscription: AlertSubscription) => void;
  removeSubscription: (id: number) => void;
  setSubscriptions: (subscriptions: AlertSubscription[]) => void;
  markFlowAsRead: (flowId: number) => void;
}

const OptionsFlowContext = createContext<OptionsFlowContextType | undefined>(undefined);

export function OptionsFlowProvider({ children }: { children: React.ReactNode }) {
  const [flows, setFlows] = useState<OptionFlow[]>([]);
  const [subscriptions, setSubscriptions] = useState<AlertSubscription[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string>();

  const addFlow = useCallback((flow: OptionFlow) => {
    setFlows(prev => {
      // Avoid duplicates
      if (prev.some(f => f.id === flow.id)) {
        return prev;
      }
      return [flow, ...prev];
    });
  }, []);

  const updateFlow = useCallback((id: number, updates: Partial<OptionFlow>) => {
    setFlows(prev =>
      prev.map(f => (f.id === id ? { ...f, ...updates } : f))
    );
  }, []);

  const removeFlow = useCallback((id: number) => {
    setFlows(prev => prev.filter(f => f.id !== id));
  }, []);

  const clearFlows = useCallback(() => {
    setFlows([]);
  }, []);

  const markFlowAsRead = useCallback((flowId: number) => {
    updateFlow(flowId, { is_alert: false });
  }, [updateFlow]);

  const addSubscription = useCallback((subscription: AlertSubscription) => {
    setSubscriptions(prev => {
      if (prev.some(s => s.id === subscription.id)) {
        return prev;
      }
      return [...prev, subscription];
    });
  }, []);

  const removeSubscription = useCallback((id: number) => {
    setSubscriptions(prev => prev.filter(s => s.id !== id));
  }, []);

  const unreadAlertCount = flows.filter(f => f.is_alert).length;

  const value: OptionsFlowContextType = {
    flows,
    subscriptions,
    unreadAlertCount,
    isLoading,
    error,
    addFlow,
    updateFlow,
    removeFlow,
    clearFlows,
    setFlows,
    addSubscription,
    removeSubscription,
    setSubscriptions,
    markFlowAsRead,
  };

  return (
    <OptionsFlowContext.Provider value={value}>
      {children}
    </OptionsFlowContext.Provider>
  );
}

export function useOptionsFlow() {
  const context = useContext(OptionsFlowContext);
  if (!context) {
    throw new Error('useOptionsFlow must be used within OptionsFlowProvider');
  }
  return context;
}
```