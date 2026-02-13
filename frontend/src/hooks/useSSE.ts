'use client';

import { useEffect, useState, useRef, useCallback } from 'react';
import type { SSEEvent, SSEEventType, AgentStatusEvent, AlertEvent, JobCompleteEvent } from '@/lib/types';

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? '';
const RECONNECT_DELAY = 5000;

interface SSEState {
  connected: boolean;
  lastEvent: SSEEvent | null;
  agentStatus: Record<string, AgentStatusEvent>;
  recentAlerts: AlertEvent[];
  recentJobCompletes: JobCompleteEvent[];
  eventLog: SSEEvent[];
}

export function useSSE() {
  const [state, setState] = useState<SSEState>({
    connected: false,
    lastEvent: null,
    agentStatus: {},
    recentAlerts: [],
    recentJobCompletes: [],
    eventLog: [],
  });

  const eventSourceRef = useRef<EventSource | null>(null);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const mountedRef = useRef(true);

  const connect = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    try {
      const es = new EventSource(`${API_BASE}/api/stream`);
      eventSourceRef.current = es;

      es.onopen = () => {
        if (mountedRef.current) {
          setState((prev) => ({ ...prev, connected: true }));
        }
      };

      es.onmessage = (event) => {
        if (!mountedRef.current) return;
        try {
          const parsed = JSON.parse(event.data) as SSEEvent;
          handleEvent(parsed);
        } catch {
          // Ignore malformed events
        }
      };

      // Listen for specific named events
      const eventTypes: SSEEventType[] = ['agent_status', 'alert', 'job_complete', 'heartbeat', 'news', 'rating_update'];
      eventTypes.forEach((type) => {
        es.addEventListener(type, (event: MessageEvent) => {
          if (!mountedRef.current) return;
          try {
            const data = JSON.parse(event.data);
            handleEvent({ type, data, timestamp: new Date().toISOString() });
          } catch {
            // Ignore malformed events
          }
        });
      });

      es.onerror = () => {
        if (!mountedRef.current) return;
        es.close();
        setState((prev) => ({ ...prev, connected: false }));
        scheduleReconnect();
      };
    } catch {
      scheduleReconnect();
    }
  }, []);

  const handleEvent = useCallback((event: SSEEvent) => {
    setState((prev) => {
      const newLog = [event, ...prev.eventLog].slice(0, 100);
      const next: SSEState = {
        ...prev,
        lastEvent: event,
        eventLog: newLog,
      };

      switch (event.type) {
        case 'agent_status': {
          const agentEvent = event.data as unknown as AgentStatusEvent;
          next.agentStatus = {
            ...prev.agentStatus,
            [agentEvent.agent_name]: agentEvent,
          };
          break;
        }
        case 'alert': {
          const alertEvent = event.data as unknown as AlertEvent;
          next.recentAlerts = [alertEvent, ...prev.recentAlerts].slice(0, 50);
          break;
        }
        case 'job_complete': {
          const jobEvent = event.data as unknown as JobCompleteEvent;
          next.recentJobCompletes = [jobEvent, ...prev.recentJobCompletes].slice(0, 50);
          break;
        }
        default:
          break;
      }

      return next;
    });
  }, []);

  const scheduleReconnect = useCallback(() => {
    if (reconnectTimerRef.current) {
      clearTimeout(reconnectTimerRef.current);
    }
    reconnectTimerRef.current = setTimeout(() => {
      if (mountedRef.current) {
        connect();
      }
    }, RECONNECT_DELAY);
  }, [connect]);

  useEffect(() => {
    mountedRef.current = true;
    connect();

    return () => {
      mountedRef.current = false;
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
      if (reconnectTimerRef.current) {
        clearTimeout(reconnectTimerRef.current);
      }
    };
  }, [connect]);

  return state;
}
