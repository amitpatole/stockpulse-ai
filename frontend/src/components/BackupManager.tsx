```typescript
/**
 * TickerPulse AI v3.0 - Backup Manager Component
 * Admin interface for database backup and restore operations
 */

import React, { useEffect, useState } from 'react';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { useBackup, Backup, BackupSchedule } from '@/hooks/useBackup';
import { useToast } from '@/hooks/use-toast';
import { formatBytes, formatDate } from '@/lib/utils';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { MoreHorizontal, Download, RotateCcw, Trash2, Plus } from 'lucide-react';

interface BackupManagerProps {
  className?: string;
}

export const BackupManager: React.FC<BackupManagerProps> = ({ className = '' }) => {
  const {
    loading,
    error,
    backups,
    schedule,
    createBackup,
    listBackups,
    deleteBackup,
    startRestore,
    getSchedule,
    updateSchedule,
  } = useBackup();

  const { toast } = useToast();

  const [notes, setNotes] = useState('');
  const [showRestoreDialog, setShowRestoreDialog] = useState(false);
  const [selectedBackupId, setSelectedBackupId] = useState<number | null>(null);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [restoreVerifyChecksum, setRestoreVerifyChecksum] = useState(true);
  const [scheduleTime, setScheduleTime] = useState('02:00');
  const [retentionDays, setRetentionDays] = useState(30);
  const [maxBackups, setMaxBackups] = useState(10);

  // Load initial data
  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    await listBackups();
    await getSchedule();
  };

  const handleCreateBackup = async () => {
    const backup = await createBackup(notes);
    if (backup) {
      toast({
        title: 'Backup Created',
        description: `${backup.filename} (${formatBytes(backup.file_size)})`,
      });
      setNotes('');
      await loadData();
    } else {
      toast({
        title: 'Backup Failed',
        description: error || 'Unknown error',
        variant: 'destructive',
      });
    }
  };

  const handleRestoreClick = (backupId: number) => {
    setSelectedBackupId(backupId);
    setShowRestoreDialog(true);
  };

  const handleRestoreConfirm = async () => {
    if (!selectedBackupId) return;

    const restoreStatus = await startRestore(
      selectedBackupId,
      restoreVerifyChecksum
    );
    if (restoreStatus) {
      toast({
        title: 'Restore Started',
        description: `Restoring ${restoreStatus.backup_filename}...`,
      });
      setShowRestoreDialog(false);
      await loadData();
    } else {
      toast({
        title: 'Restore Failed',
        description: error || 'Unknown error',
        variant: 'destructive',
      });
    }
  };

  const handleDeleteClick = (backupId: number) => {
    setSelectedBackupId(backupId);
    setShowDeleteDialog(true);
  };

  const handleDeleteConfirm = async () => {
    if (!selectedBackupId) return;

    const success = await deleteBackup(selectedBackupId);
    if (success) {
      toast({
        title: 'Backup Deleted',
        description: 'Backup removed successfully',
      });
      setShowDeleteDialog(false);
      await loadData();
    } else {
      toast({
        title: 'Delete Failed',
        description: error || 'Unknown error',
        variant: 'destructive',
      });
    }
  };

  const handleUpdateSchedule = async () => {
    const updated = await updateSchedule({
      enabled: schedule?.enabled ?? false,
      schedule_time: scheduleTime,
      retention_days: retentionDays,
      max_backups: maxBackups,
    });
    if (updated) {
      toast({
        title: 'Schedule Updated',
        description: 'Backup schedule saved successfully',
      });
    } else {
      toast({
        title: 'Update Failed',
        description: error || 'Unknown error',
        variant: 'destructive',
      });
    }
  };

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Automatic Backups Section */}
      <Card>
        <CardHeader>
          <CardTitle>Automatic Backups</CardTitle>
          <CardDescription>
            Configure scheduled backup settings
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center space-x-2">
            <Switch
              id="enable-auto-backup"
              checked={schedule?.enabled ?? false}
              onCheckedChange={(checked) => {
                if (schedule) {
                  updateSchedule({ ...schedule, enabled: checked });
                }
              }}
            />
            <Label htmlFor="enable-auto-backup">Enable Scheduled Backups</Label>
          </div>

          {schedule?.next_scheduled_run && (
            <div className="text-sm text-gray-600">
              Next scheduled run: {formatDate(schedule.next_scheduled_run)}
            </div>
          )}

          <div className="grid grid-cols-3 gap-4">
            <div>
              <Label htmlFor="schedule-time">Backup Time (HH:MM)</Label>
              <Input
                id="schedule-time"
                type="time"
                value={scheduleTime}
                onChange={(e) => setScheduleTime(e.target.value)}
              />
            </div>
            <div>
              <Label htmlFor="retention-days">Retention (days)</Label>
              <Input
                id="retention-days"
                type="number"
                min="1"
                max="365"
                value={retentionDays}
                onChange={(e) => setRetentionDays(parseInt(e.target.value) || 30)}
              />
            </div>
            <div>
              <Label htmlFor="max-backups">Max Backups</Label>
              <Input
                id="max-backups"
                type="number"
                min="1"
                max="100"
                value={maxBackups}
                onChange={(e) => setMaxBackups(parseInt(e.target.value) || 10)}
              />
            </div>
          </div>

          <Button
            onClick={handleUpdateSchedule}
            disabled={loading}
            className="w-full"
          >
            Save Schedule
          </Button>
        </CardContent>
      </Card>

      {/* Manual Backup Section */}
      <Card>
        <CardHeader>
          <CardTitle>Manual Backup</CardTitle>
          <CardDescription>
            Create a backup immediately
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <Label htmlFor="backup-notes">Notes (optional)</Label>
            <Input
              id="backup-notes"
              placeholder="Add notes for this backup..."
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
            />
          </div>

          <Button
            onClick={handleCreateBackup}
            disabled={loading}
            className="w-full"
            size="lg"
          >
            <Plus className="mr-2 h-4 w-4" />
            Create Backup Now
          </Button>
        </CardContent>
      </Card>

      {/* Backups List Section */}
      <Card>
        <CardHeader>
          <CardTitle>Backup History</CardTitle>
          <CardDescription>
            {backups.length} backup{backups.length !== 1 ? 's' : ''}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {backups.length === 0 ? (
            <div className="text-center text-gray-500 py-8">
              No backups yet. Create one to get started.
            </div>
          ) : (
            <div className="space-y-2">
              {backups.map((backup) => (
                <div
                  key={backup.id}
                  className="flex items-center justify-between p-3 border rounded-lg hover:bg-gray-50"
                >
                  <div className="flex-1">
                    <div className="font-medium text-sm">
                      {formatDate(backup.created_at)}
                    </div>
                    <div className="text-xs text-gray-600 space-x-2">
                      <span>{formatBytes(backup.file_size)}</span>
                      <span>•</span>
                      <span>{backup.is_manual ? 'Manual' : 'Automatic'}</span>
                      {backup.notes && (
                        <>
                          <span>•</span>
                          <span>{backup.notes}</span>
                        </>
                      )}
                    </div>
                  </div>

                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" size="sm">
                        <MoreHorizontal className="h-4 w-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem
                        onClick={() => handleRestoreClick(backup.id)}
                      >
                        <RotateCcw className="mr-2 h-4 w-4" />
                        Restore
                      </DropdownMenuItem>
                      <DropdownMenuItem
                        onClick={() => handleDeleteClick(backup.id)}
                        className="text-red-600"
                      >
                        <Trash2 className="mr-2 h-4 w-4" />
                        Delete
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Restore Confirmation Dialog */}
      <AlertDialog open={showRestoreDialog} onOpenChange={setShowRestoreDialog}>
        <AlertDialogContent>
          <AlertDialogTitle>Restore Database?</AlertDialogTitle>
          <AlertDialogDescription>
            <div className="space-y-3">
              <p>
                This will replace your current database with the selected backup.
                Your current database will be automatically backed up first.
              </p>
              <div className="flex items-center space-x-2">
                <Switch
                  id="verify-checksum"
                  checked={restoreVerifyChecksum}
                  onCheckedChange={setRestoreVerifyChecksum}
                />
                <Label htmlFor="verify-checksum">
                  Verify backup integrity before restoring
                </Label>
              </div>
              <p className="text-sm text-red-600">
                This action cannot be undone. Proceed with caution.
              </p>
            </div>
          </AlertDialogDescription>
          <div className="flex gap-2 justify-end">
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleRestoreConfirm}
              className="bg-red-600 hover:bg-red-700"
            >
              Restore
            </AlertDialogAction>
          </div>
        </AlertDialogContent>
      </AlertDialog>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <AlertDialogContent>
          <AlertDialogTitle>Delete Backup?</AlertDialogTitle>
          <AlertDialogDescription>
            This backup will be permanently deleted. This action cannot be undone.
          </AlertDialogDescription>
          <div className="flex gap-2 justify-end">
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDeleteConfirm}
              className="bg-red-600 hover:bg-red-700"
            >
              Delete
            </AlertDialogAction>
          </div>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
};
```