/**
 * StockPulse AI - Auto-Update Manager
 *
 * Uses electron-updater to check GitHub Releases for new versions,
 * download silently in the background, and prompt the user to restart.
 */

import { autoUpdater, UpdateInfo, ProgressInfo } from 'electron-updater';
import { BrowserWindow, dialog, app } from 'electron';
import log from 'electron-log';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type UpdateStatus =
  | { state: 'idle' }
  | { state: 'checking' }
  | { state: 'available'; version: string }
  | { state: 'downloading'; percent: number }
  | { state: 'ready'; version: string }
  | { state: 'error'; message: string }
  | { state: 'up-to-date' };

// ---------------------------------------------------------------------------
// State
// ---------------------------------------------------------------------------

let status: UpdateStatus = { state: 'idle' };
let mainWindowRef: BrowserWindow | null = null;
let onStatusChange: (() => void) | null = null;

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

export function getUpdateStatus(): UpdateStatus {
  return status;
}

export function setOnStatusChange(callback: () => void): void {
  onStatusChange = callback;
}

export function initAutoUpdater(mainWindow: BrowserWindow): void {
  mainWindowRef = mainWindow;

  // Configure electron-updater
  autoUpdater.logger = log;
  autoUpdater.autoDownload = true;
  autoUpdater.autoInstallOnAppQuit = true;

  // Event handlers
  autoUpdater.on('checking-for-update', () => {
    log.info('[updater] Checking for updates...');
    setStatus({ state: 'checking' });
  });

  autoUpdater.on('update-available', (info: UpdateInfo) => {
    log.info(`[updater] Update available: v${info.version}`);
    setStatus({ state: 'available', version: info.version });
  });

  autoUpdater.on('update-not-available', (_info: UpdateInfo) => {
    log.info('[updater] App is up to date');
    setStatus({ state: 'up-to-date' });
    setTimeout(() => setStatus({ state: 'idle' }), 30_000);
  });

  autoUpdater.on('download-progress', (progress: ProgressInfo) => {
    const pct = Math.round(progress.percent);
    log.info(`[updater] Download progress: ${pct}%`);
    setStatus({ state: 'downloading', percent: pct });
  });

  autoUpdater.on('update-downloaded', (info: UpdateInfo) => {
    log.info(`[updater] Update downloaded: v${info.version}`);
    setStatus({ state: 'ready', version: info.version });
    promptUserToRestart(info.version);
  });

  autoUpdater.on('error', (err: Error) => {
    log.error('[updater] Error:', err.message);
    setStatus({ state: 'error', message: err.message });
    setTimeout(() => setStatus({ state: 'idle' }), 60_000);
  });

  // Initial check — delayed so startup finishes first
  setTimeout(() => {
    log.info('[updater] Running startup update check');
    autoUpdater.checkForUpdates().catch((err) => {
      log.warn('[updater] Startup check failed:', err.message);
    });
  }, 10_000);

  // Periodic check every 4 hours
  setInterval(() => {
    log.info('[updater] Running periodic update check');
    autoUpdater.checkForUpdates().catch((err) => {
      log.warn('[updater] Periodic check failed:', err.message);
    });
  }, 4 * 60 * 60 * 1000);
}

export function checkForUpdatesManual(): void {
  if (status.state === 'checking' || status.state === 'downloading') {
    return;
  }

  autoUpdater.checkForUpdates().catch((err) => {
    log.error('[updater] Manual check failed:', err.message);
    if (mainWindowRef && !mainWindowRef.isDestroyed()) {
      dialog.showMessageBox(mainWindowRef, {
        type: 'error',
        title: 'Update Check Failed',
        message: 'Could not check for updates.',
        detail: err.message,
        buttons: ['OK'],
      });
    }
  });
}

// ---------------------------------------------------------------------------
// Internal
// ---------------------------------------------------------------------------

function setStatus(newStatus: UpdateStatus): void {
  status = newStatus;
  onStatusChange?.();
}

function promptUserToRestart(version: string): void {
  if (!mainWindowRef || mainWindowRef.isDestroyed()) return;

  dialog
    .showMessageBox(mainWindowRef, {
      type: 'info',
      title: 'Update Ready',
      message: `StockPulse AI v${version} is ready to install.`,
      detail:
        'The update has been downloaded. Restart now to apply it?\n\n' +
        'All running services will be stopped gracefully.',
      buttons: ['Restart Now', 'Later'],
      defaultId: 0,
      cancelId: 1,
    })
    .then(({ response }) => {
      if (response === 0) {
        log.info('[updater] User chose to restart now');
        (app as any).isQuitting = true;
        setTimeout(() => {
          autoUpdater.quitAndInstall(false, true);
        }, 2000);
      } else {
        log.info('[updater] User deferred update — will install on next quit');
      }
    });
}
