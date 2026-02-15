import { Tray, Menu, nativeImage, BrowserWindow, app } from 'electron';
import * as path from 'path';

let tray: Tray | null = null;

export function setupTray(mainWindow: BrowserWindow): void {
  const iconPath = app.isPackaged
    ? path.join(process.resourcesPath, 'assets', 'tray-icon.png')
    : path.join(__dirname, '..', '..', 'assets', 'tray-icon.png');

  tray = new Tray(nativeImage.createFromPath(iconPath));

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
    {
      label: 'Quit',
      click: () => {
        (app as any).isQuitting = true;
        app.quit();
      },
    },
  ]);

  tray.setToolTip('StockPulse AI v3.0');
  tray.setContextMenu(contextMenu);

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
