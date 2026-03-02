```typescript
/**
 * Tests for BackupManager Component
 */

import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BackupManager } from '../BackupManager';
import * as useBackupModule from '@/hooks/useBackup';
import { useToast } from '@/hooks/use-toast';

// Mock the hooks
vi.mock('@/hooks/useBackup');
vi.mock('@/hooks/use-toast');
vi.mock('@/components/ui/card', () => ({
  Card: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="card">{children}</div>
  ),
  CardHeader: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="card-header">{children}</div>
  ),
  CardTitle: ({ children }: { children: React.ReactNode }) => (
    <h2>{children}</h2>
  ),
  CardDescription: ({ children }: { children: React.ReactNode }) => (
    <p>{children}</p>
  ),
  CardContent: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="card-content">{children}</div>
  ),
}));

vi.mock('@/components/ui/button', () => ({
  Button: ({ children, ...props }: any) => (
    <button {...props}>{children}</button>
  ),
}));

vi.mock('@/components/ui/input', () => ({
  Input: (props: any) => <input {...props} />,
}));

vi.mock('@/components/ui/label', () => ({
  Label: ({ children, ...props }: any) => <label {...props}>{children}</label>,
}));

vi.mock('@/components/ui/switch', () => ({
  Switch: (props: any) => <input type="checkbox" {...props} />,
}));

vi.mock('@/components/ui/alert-dialog', () => ({
  AlertDialog: ({ children, open }: any) =>
    open ? <div data-testid="alert-dialog">{children}</div> : null,
  AlertDialogContent: ({ children }: any) => <div>{children}</div>,
  AlertDialogTitle: ({ children }: any) => <h3>{children}</h3>,
  AlertDialogDescription: ({ children }: any) => <div>{children}</div>,
  AlertDialogAction: ({ children, ...props }: any) => (
    <button {...props}>{children}</button>
  ),
  AlertDialogCancel: ({ children, ...props }: any) => (
    <button {...props}>{children}</button>
  ),
}));

vi.mock('@/components/ui/dropdown-menu', () => ({
  DropdownMenu: ({ children }: any) => <div>{children}</div>,
  DropdownMenuTrigger: ({ children }: any) => <div>{children}</div>,
  DropdownMenuContent: ({ children }: any) => <div>{children}</div>,
  DropdownMenuItem: ({ children, ...props }: any) => (
    <button {...props}>{children}</button>
  ),
}));

const mockToast = vi.fn();

describe('BackupManager', () => {
  beforeEach(() => {
    vi.clearAllMocks();

    (useToast as any).mockReturnValue({ toast: mockToast });
  });

  it('renders backup manager sections', () => {
    (useBackupModule.useBackup as any).mockReturnValue({
      loading: false,
      error: null,
      backups: [],
      schedule: {
        enabled: false,
        schedule_time: '02:00',
        retention_days: 30,
        max_backups: 10,
      },
      createBackup: vi.fn(),
      listBackups: vi.fn().mockResolvedValue([]),
      deleteBackup: vi.fn(),
      startRestore: vi.fn(),
      getSchedule: vi.fn().mockResolvedValue({}),
      updateSchedule: vi.fn(),
    });

    render(<BackupManager />);

    expect(screen.getByText('Automatic Backups')).toBeInTheDocument();
    expect(screen.getByText('Manual Backup')).toBeInTheDocument();
    expect(screen.getByText('Backup History')).toBeInTheDocument();
  });

  it('creates backup with notes', async () => {
    const mockCreateBackup = vi.fn().mockResolvedValue({
      id: 1,
      filename: 'stock_news.backup.20260302_170530.db',
      file_size: 15728640,
      created_at: '2026-03-02T17:05:30Z',
      notes: 'Test backup',
      is_manual: true,
      checksum: 'abc123',
    });

    (useBackupModule.useBackup as any).mockReturnValue({
      loading: false,
      error: null,
      backups: [],
      schedule: {
        enabled: false,
        schedule_time: '02:00',
        retention_days: 30,
        max_backups: 10,
      },
      createBackup: mockCreateBackup,
      listBackups: vi.fn().mockResolvedValue([]),
      deleteBackup: vi.fn(),
      startRestore: vi.fn(),
      getSchedule: vi.fn().mockResolvedValue({}),
      updateSchedule: vi.fn(),
    });

    render(<BackupManager />);

    const notesInput = screen.getByPlaceholderText('Add notes for this backup...');
    const createButton = screen.getByText('Create Backup Now');

    await userEvent.type(notesInput, 'Test backup');
    fireEvent.click(createButton);

    await waitFor(() => {
      expect(mockCreateBackup).toHaveBeenCalledWith('Test backup');
    });
  });

  it('displays list of backups', () => {
    const mockBackups = [
      {
        id: 1,
        filename: 'stock_news.backup.20260302_170530.db',
        file_size: 15728640,
        created_at: '2026-03-02T17:05:30Z',
        notes: 'Manual backup',
        is_manual: true,
        checksum: 'abc123',
      },
    ];

    (useBackupModule.useBackup as any).mockReturnValue({
      loading: false,
      error: null,
      backups: mockBackups,
      schedule: {
        enabled: false,
        schedule_time: '02:00',
        retention_days: 30,
        max_backups: 10,
      },
      createBackup: vi.fn(),
      listBackups: vi.fn().mockResolvedValue(mockBackups),
      deleteBackup: vi.fn(),
      startRestore: vi.fn(),
      getSchedule: vi.fn().mockResolvedValue({}),
      updateSchedule: vi.fn(),
    });

    render(<BackupManager />);

    expect(screen.getByText(/Manual backup/)).toBeInTheDocument();
  });

  it('shows restore confirmation dialog', async () => {
    const mockBackups = [
      {
        id: 1,
        filename: 'stock_news.backup.20260302_170530.db',
        file_size: 15728640,
        created_at: '2026-03-02T17:05:30Z',
        notes: 'Manual backup',
        is_manual: true,
        checksum: 'abc123',
      },
    ];

    (useBackupModule.useBackup as any).mockReturnValue({
      loading: false,
      error: null,
      backups: mockBackups,
      schedule: {
        enabled: false,
        schedule_time: '02:00',
        retention_days: 30,
        max_backups: 10,
      },
      createBackup: vi.fn(),
      listBackups: vi.fn().mockResolvedValue(mockBackups),
      deleteBackup: vi.fn(),
      startRestore: vi.fn().mockResolvedValue({ restore_id: 'test' }),
      getSchedule: vi.fn().mockResolvedValue({}),
      updateSchedule: vi.fn(),
    });

    render(<BackupManager />);

    const restoreButton = screen.getByText('Restore');
    fireEvent.click(restoreButton);

    await waitFor(() => {
      expect(screen.getByText('Restore Database?')).toBeInTheDocument();
    });
  });
});
```