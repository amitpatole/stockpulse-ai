```typescript
/**
 * TickerPulse AI v3.0 - Backup Management Hook
 * Handles backup API calls and state management
 */

import { useState, useCallback } from 'react';

export interface Backup {
  id: number;
  filename: string;
  file_size: number;
  created_at: string;
  notes: string;
  is_manual: boolean;
  checksum: string;
}

export interface BackupSchedule {
  enabled: boolean;
  schedule_time: string;
  retention_days: number;
  max_backups: number;
  next_scheduled_run?: string;
}

export interface BackupsListResponse {
  data: Backup[];
  meta: {
    total_count: number;
    limit: number;
    offset: number;
  };
}

export interface BackupResponse {
  data: Backup;
  meta: Record<string, unknown>;
}

export interface RestoreStatus {
  restore_id: string;
  status: 'in_progress' | 'completed' | 'failed';
  backup_id: number;
  backup_filename: string;
  started_at?: string;
  completed_at?: string;
  error?: string;
  pre_restore_backup_id?: number;
}

export const useBackup = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [backups, setBackups] = useState<Backup[]>([]);
  const [schedule, setSchedule] = useState<BackupSchedule | null>(null);

  const createBackup = useCallback(
    async (notes?: string): Promise<Backup | null> => {
      setLoading(true);
      setError(null);
      try {
        const response = await fetch('/api/admin/backups', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ notes: notes || '' }),
        });

        if (!response.ok) {
          const data = await response.json();
          throw new Error(data.error || 'Failed to create backup');
        }

        const data: BackupResponse = await response.json();
        return data.data;
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Unknown error';
        setError(message);
        return null;
      } finally {
        setLoading(false);
      }
    },
    []
  );

  const listBackups = useCallback(
    async (limit = 50, offset = 0): Promise<Backup[]> => {
      setLoading(true);
      setError(null);
      try {
        const response = await fetch(
          `/api/admin/backups?limit=${limit}&offset=${offset}`
        );

        if (!response.ok) {
          const data = await response.json();
          throw new Error(data.error || 'Failed to list backups');
        }

        const data: BackupsListResponse = await response.json();
        setBackups(data.data);
        return data.data;
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Unknown error';
        setError(message);
        return [];
      } finally {
        setLoading(false);
      }
    },
    []
  );

  const deleteBackup = useCallback(
    async (backupId: number): Promise<boolean> => {
      setLoading(true);
      setError(null);
      try {
        const response = await fetch(`/api/admin/backups/${backupId}`, {
          method: 'DELETE',
        });

        if (!response.ok) {
          const data = await response.json();
          throw new Error(data.error || 'Failed to delete backup');
        }

        return true;
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Unknown error';
        setError(message);
        return false;
      } finally {
        setLoading(false);
      }
    },
    []
  );

  const startRestore = useCallback(
    async (
      backupId: number,
      verifyChecksum = true
    ): Promise<RestoreStatus | null> => {
      setLoading(true);
      setError(null);
      try {
        const response = await fetch(
          `/api/admin/backups/${backupId}/restore`,
          {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ verify_checksum: verifyChecksum }),
          }
        );

        if (!response.ok) {
          const data = await response.json();
          throw new Error(data.error || 'Failed to start restore');
        }

        const data = await response.json();
        return data.data as RestoreStatus;
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Unknown error';
        setError(message);
        return null;
      } finally {
        setLoading(false);
      }
    },
    []
  );

  const getRestoreStatus = useCallback(
    async (restoreId: string): Promise<RestoreStatus | null> => {
      try {
        const response = await fetch(`/api/admin/restores/${restoreId}`);

        if (!response.ok) {
          const data = await response.json();
          throw new Error(data.error || 'Failed to get restore status');
        }

        const data = await response.json();
        return data.data as RestoreStatus;
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Unknown error';
        setError(message);
        return null;
      }
    },
    []
  );

  const getSchedule = useCallback(async (): Promise<BackupSchedule | null> => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch('/api/admin/backup-schedule');

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.error || 'Failed to get schedule');
      }

      const data = await response.json();
      setSchedule(data.data);
      return data.data as BackupSchedule;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Unknown error';
      setError(message);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  const updateSchedule = useCallback(
    async (config: Partial<BackupSchedule>): Promise<BackupSchedule | null> => {
      setLoading(true);
      setError(null);
      try {
        const response = await fetch('/api/admin/backup-schedule', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(config),
        });

        if (!response.ok) {
          const data = await response.json();
          throw new Error(data.error || 'Failed to update schedule');
        }

        const data = await response.json();
        setSchedule(data.data);
        return data.data as BackupSchedule;
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Unknown error';
        setError(message);
        return null;
      } finally {
        setLoading(false);
      }
    },
    []
  );

  return {
    loading,
    error,
    backups,
    schedule,
    createBackup,
    listBackups,
    deleteBackup,
    startRestore,
    getRestoreStatus,
    getSchedule,
    updateSchedule,
  };
};
```