/**
 * TickerPulse AI - Electron Main Process
 *
 * Manages the application lifecycle:
 * 1. First run → setup wizard
 * 2. Normal run → start backend, start frontend, load dashboard
 * 3. System tray for background operation
 */

import { app, BrowserWindow, ipcMain, Menu, dialog, shell } from 'electron';
import * as path from 'path';
import * as fs from 'fs';
import log from 'electron-log';

import { getAppDataPath, isFirstRun, getLogsPath } from './paths';
import { BackendManager } from './backend-manager';
import { FrontendManager } from './frontend-manager';
import { setupTray, rebuildTrayMenu } from './tray';
import { registerIpcHandlers } from './ipc-handlers';
import { initAutoUpdater, checkForUpdatesManual, setOnStatusChange } from './updater';

let mainWindow: BrowserWindow | null = null;
let wizardWindow: BrowserWindow | null = null;
let backendManager: BackendManager | null = null;
let frontendManager: FrontendManager | null = null;

// Configure logging
log.transports.file.resolvePathFn = () =>
  path.join(getAppDataPath(), 'logs', 'electron.log');

// ---------------------------------------------------------------------------
// Application Menu
// ---------------------------------------------------------------------------

function buildAppMenu(): void {
  const template: Electron.MenuItemConstructorOptions[] = [
    {
      label: 'File',
      submenu: [
        {
          label: 'Settings',
          accelerator: 'CmdOrCtrl+,',
          click: () => {
            if (mainWindow) {
              mainWindow.show();
              mainWindow.loadURL('http://localhost:3000/settings');
            }
          },
        },
        { type: 'separator' },
        {
          label: 'Quit',
          accelerator: 'CmdOrCtrl+Q',
          click: () => {
            (app as any).isQuitting = true;
            app.quit();
          },
        },
      ],
    },
    {
      label: 'View',
      submenu: [
        {
          label: 'Dashboard',
          accelerator: 'CmdOrCtrl+1',
          click: () => {
            if (mainWindow) {
              mainWindow.show();
              mainWindow.loadURL('http://localhost:3000');
            }
          },
        },
        {
          label: 'Agents',
          accelerator: 'CmdOrCtrl+2',
          click: () => {
            if (mainWindow) {
              mainWindow.show();
              mainWindow.loadURL('http://localhost:3000/agents');
            }
          },
        },
        {
          label: 'Research',
          accelerator: 'CmdOrCtrl+3',
          click: () => {
            if (mainWindow) {
              mainWindow.show();
              mainWindow.loadURL('http://localhost:3000/research');
            }
          },
        },
        { type: 'separator' },
        { role: 'reload' },
        { role: 'toggleDevTools' },
        { type: 'separator' },
        { role: 'resetZoom' },
        { role: 'zoomIn' },
        { role: 'zoomOut' },
        { type: 'separator' },
        { role: 'togglefullscreen' },
      ],
    },
    {
      label: 'Help',
      submenu: [
        {
          label: 'Check for Updates...',
          click: () => {
            checkForUpdatesManual();
          },
        },
        { type: 'separator' },
        {
          label: 'About TickerPulse AI',
          click: () => {
            dialog.showMessageBox({
              type: 'info',
              title: 'About TickerPulse AI',
              message: 'TickerPulse AI',
              detail: [
                `Version: ${app.getVersion()}`,
                '',
                'Multi-agent AI stock research and monitoring tool.',
                '',
                'This is a research/monitoring tool, NOT a trading system.',
                'No trades are executed. Human makes all trading decisions.',
                '',
                `Data: ${getAppDataPath()}`,
                `Logs: ${getLogsPath()}`,
              ].join('\n'),
              buttons: ['OK'],
            });
          },
        },
        { type: 'separator' },
        {
          label: 'Open Logs Folder',
          click: () => {
            shell.openPath(getLogsPath());
          },
        },
        {
          label: 'Open Data Folder',
          click: () => {
            shell.openPath(getAppDataPath());
          },
        },
      ],
    },
  ];

  const menu = Menu.buildFromTemplate(template);
  Menu.setApplicationMenu(menu);
}

// ---------------------------------------------------------------------------
// App lifecycle
// ---------------------------------------------------------------------------

app.whenReady().then(async () => {
  log.info('TickerPulse AI starting...');

  buildAppMenu();
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

  // __dirname = dist/main/ — go up two levels to reach root (both dev and packaged)
  const wizardPath = path.join(__dirname, '..', '..', 'wizard', 'index.html');

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
    title: 'TickerPulse AI',
    show: false,
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
    },
  });

  // Show splash while services start
  const splashPath = path.join(__dirname, '..', '..', 'wizard', 'splash.html');

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

    // Initialize auto-updater and wire status changes to tray
    initAutoUpdater(mainWindow);
    setOnStatusChange(() => rebuildTrayMenu());

    log.info('TickerPulse AI is running');
  } catch (err) {
    log.error('Failed to start services:', err);
    showErrorPage(String(err));
  }

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

// ---------------------------------------------------------------------------
// Error Page
// ---------------------------------------------------------------------------

function showErrorPage(errorMessage: string): void {
  if (!mainWindow) return;

  const logsDir = getLogsPath();
  const errorHtml = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>TickerPulse AI - Startup Error</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      background: #0f172a;
      color: #e2e8f0;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      padding: 60px;
    }
    h1 { color: #f87171; margin-bottom: 16px; }
    p { margin-bottom: 12px; color: #94a3b8; line-height: 1.6; }
    pre {
      background: #1e293b;
      border: 1px solid #334155;
      border-radius: 8px;
      padding: 16px;
      color: #f87171;
      font-size: 13px;
      white-space: pre-wrap;
      word-wrap: break-word;
      margin: 16px 0;
      max-height: 200px;
      overflow-y: auto;
    }
    .path {
      background: #1e293b;
      padding: 4px 8px;
      border-radius: 4px;
      font-family: monospace;
      font-size: 13px;
      color: #60a5fa;
    }
    .hint {
      margin-top: 24px;
      padding: 16px;
      background: rgba(37, 99, 235, 0.1);
      border: 1px solid rgba(37, 99, 235, 0.3);
      border-radius: 8px;
    }
    .hint h3 { color: #60a5fa; margin-bottom: 8px; }
    .hint li { color: #94a3b8; margin: 4px 0 4px 20px; }
  </style>
</head>
<body>
  <h1>Startup Error</h1>
  <p>TickerPulse AI failed to start its services.</p>
  <pre>${errorMessage.replace(/</g, '&lt;').replace(/>/g, '&gt;')}</pre>
  <p>Check the logs at: <span class="path">${logsDir.replace(/\\/g, '\\\\')}</span></p>
  <div class="hint">
    <h3>Troubleshooting</h3>
    <ul>
      <li>Check that ports 5000 and 3000 are not in use by another application</li>
      <li>Try restarting TickerPulse AI</li>
      <li>Check the electron.log file in the logs folder for details</li>
      <li>Use Help > Open Logs Folder from the menu to view logs</li>
    </ul>
  </div>
</body>
</html>`;

  // Write error page to temp file (data: URLs can be blocked by CSP)
  const errorPath = path.join(getAppDataPath(), 'error.html');
  fs.writeFileSync(errorPath, errorHtml, 'utf-8');
  mainWindow.loadFile(errorPath);
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
