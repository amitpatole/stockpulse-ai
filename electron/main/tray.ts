import { Tray, Menu, nativeImage, BrowserWindow, app } from 'electron';
import * as path from 'path';
import { autoUpdater } from 'electron-updater';
import { getUpdateStatus, checkForUpdatesManual, UpdateStatus } from './updater';

let tray: Tray | null = null;
let mainWindowRef: BrowserWindow | null = null;

export function setupTray(mainWindow: BrowserWindow): void {
  mainWindowRef = mainWindow;

  // __dirname = dist/main/ — go up two levels to reach root (both dev and packaged)
  const iconPath = path.join(__dirname, '..', '..', 'assets', 'tray-icon.png');

  tray = new Tray(nativeImage.createFromPath(iconPath));
  tray.setToolTip(`StockPulse AI v${app.getVersion()}`);

  buildTrayMenu();

  // Click tray icon to show window
  tray.on('click', () => {
    mainWindow.show();
    mainWindow.focus();
  });

  // Minimize to tray instead of closing
  mainWindow.on('close', (event) => {
    if (!(app as any).isQuitting) {
      event.preventDefault();
      mainWindow.hide();
    }
  });
}

export function rebuildTrayMenu(): void {
  buildTrayMenu();
}

function buildTrayMenu(): void {
  if (!tray || !mainWindowRef) return;
  const mainWindow = mainWindowRef;

  const status = getUpdateStatus();

  const contextMenu = Menu.buildFromTemplate([
    {
      label: 'Show StockPulse AI',
      click: () => {
        mainWindow.show();
        mainWindow.focus();
      },
    },
    { type: 'separator' },
    {
      label: 'Dashboard',
      click: () => {
        mainWindow.show();
        mainWindow.loadURL('http://localhost:3000');
      },
    },
    {
      label: 'Agents',
      click: () => {
        mainWindow.show();
        mainWindow.loadURL('http://localhost:3000/agents');
      },
    },
    {
      label: 'Settings',
      click: () => {
        mainWindow.show();
        mainWindow.loadURL('http://localhost:3000/settings');
      },
    },
    { type: 'separator' },
    getUpdateMenuItem(status),
    { type: 'separator' },
    {
      label: 'Quit',
      click: () => {
        (app as any).isQuitting = true;
        app.quit();
      },
    },
  ]);

  tray.setContextMenu(contextMenu);
}

function getUpdateMenuItem(status: UpdateStatus): Electron.MenuItemConstructorOptions {
  switch (status.state) {
    case 'checking':
      return { label: 'Checking for updates...', enabled: false };
    case 'available':
      return { label: `Downloading v${status.version}...`, enabled: false };
    case 'downloading':
      return { label: `Downloading update... ${status.percent}%`, enabled: false };
    case 'ready':
      return {
        label: `Restart to update (v${status.version})`,
        click: () => {
          (app as any).isQuitting = true;
          autoUpdater.quitAndInstall(false, true);
        },
      };
    case 'error':
      return {
        label: 'Update check failed — Retry',
        click: () => checkForUpdatesManual(),
      };
    case 'up-to-date':
      return { label: 'Up to date', enabled: false };
    case 'idle':
    default:
      return {
        label: 'Check for Updates',
        click: () => checkForUpdatesManual(),
      };
  }
}
