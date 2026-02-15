/**
 * StockPulse AI - Electron Main Process
 *
 * Manages the application lifecycle:
 * 1. First run → setup wizard
 * 2. Normal run → start backend, start frontend, load dashboard
 * 3. System tray for background operation
 */

import { app, BrowserWindow, ipcMain } from 'electron';
import * as path from 'path';
import log from 'electron-log';

import { getAppDataPath, isFirstRun } from './paths';
import { BackendManager } from './backend-manager';
import { FrontendManager } from './frontend-manager';
import { setupTray } from './tray';
import { registerIpcHandlers } from './ipc-handlers';

let mainWindow: BrowserWindow | null = null;
let wizardWindow: BrowserWindow | null = null;
let backendManager: BackendManager | null = null;
let frontendManager: FrontendManager | null = null;

// Configure logging
log.transports.file.resolvePathFn = () =>
  path.join(getAppDataPath(), 'logs', 'electron.log');

// ---------------------------------------------------------------------------
// App lifecycle
// ---------------------------------------------------------------------------

app.whenReady().then(async () => {
  log.info('StockPulse AI starting...');

  registerIpcHandlers();

  // Window control IPC for frameless wizard
  ipcMain.on('window:minimize', () => wizardWindow?.minimize());
  ipcMain.on('window:close', () => wizardWindow?.close());

  if (isFirstRun()) {
    log.info('First run detected — showing setup wizard');
    showWizard();
  } else {
    log.info('Existing setup found — starting app');
    await startApp();
  }
});

app.on('window-all-closed', () => {
  // On macOS, apps stay open until Cmd+Q. On Windows/Linux, quit.
  if (process.platform !== 'darwin') {
    shutdown();
  }
});

app.on('before-quit', () => {
  (app as any).isQuitting = true;
  shutdown();
});

// ---------------------------------------------------------------------------
// Setup Wizard
// ---------------------------------------------------------------------------

function showWizard(): void {
  wizardWindow = new BrowserWindow({
    width: 720,
    height: 640,
    resizable: false,
    frame: false,
    webPreferences: {
      preload: path.join(__dirname, '..', 'preload', 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
    },
  });

  const wizardPath = app.isPackaged
    ? path.join(__dirname, '..', 'wizard', 'index.html')
    : path.join(__dirname, '..', '..', 'wizard', 'index.html');

  wizardWindow.loadFile(wizardPath);

  // When the wizard signals completion
  ipcMain.once('wizard:complete', async () => {
    log.info('Wizard completed — launching app');
    wizardWindow?.close();
    wizardWindow = null;
    await startApp();
  });

  wizardWindow.on('closed', () => {
    wizardWindow = null;
    // If wizard was closed without completing, quit the app
    if (!mainWindow) {
      app.quit();
    }
  });
}

// ---------------------------------------------------------------------------
// Main App
// ---------------------------------------------------------------------------

async function startApp(): Promise<void> {
  // Create main window with splash
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1024,
    minHeight: 700,
    title: 'StockPulse AI',
    show: false,
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
    },
  });

  // Show splash while services start
  const splashPath = app.isPackaged
    ? path.join(__dirname, '..', 'wizard', 'splash.html')
    : path.join(__dirname, '..', '..', 'wizard', 'splash.html');

  mainWindow.loadFile(splashPath);
  mainWindow.show();

  try {
    // Start backend
    log.info('Starting backend...');
    backendManager = new BackendManager();
    await backendManager.start();
    await backendManager.waitForHealth();
    log.info('Backend ready');

    // Start frontend
    log.info('Starting frontend...');
    frontendManager = new FrontendManager();
    await frontendManager.start();
    await frontendManager.waitForReady();
    log.info('Frontend ready');

    // Load the dashboard
    mainWindow.loadURL('http://localhost:3000');

    // Setup system tray
    setupTray(mainWindow);

    log.info('StockPulse AI is running');
  } catch (err) {
    log.error('Failed to start services:', err);
    mainWindow.loadURL(
      `data:text/html,<html><body style="background:#0f172a;color:#e2e8f0;font-family:sans-serif;padding:40px">
        <h1>Startup Error</h1>
        <p>StockPulse AI failed to start its services.</p>
        <pre style="color:#f87171">${String(err)}</pre>
        <p>Check the logs at: ${path.join(getAppDataPath(), 'logs')}</p>
      </body></html>`
    );
  }

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

// ---------------------------------------------------------------------------
// Shutdown
// ---------------------------------------------------------------------------

async function shutdown(): Promise<void> {
  log.info('Shutting down...');

  if (frontendManager) {
    await frontendManager.stop();
    frontendManager = null;
  }

  if (backendManager) {
    await backendManager.stop();
    backendManager = null;
  }

  log.info('Shutdown complete');
}
