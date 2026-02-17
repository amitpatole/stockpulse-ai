import { contextBridge, ipcRenderer } from 'electron';

contextBridge.exposeInMainWorld('tickerpulse', {
  /**
   * Test an AI provider API key from the wizard.
   */
  testAiProvider: (args: { provider: string; api_key: string }) =>
    ipcRenderer.invoke('wizard:test-ai-provider', args),

  /**
   * Save all wizard configuration and mark setup as complete.
   */
  saveConfig: (config: any) => ipcRenderer.invoke('wizard:save-config', config),

  /**
   * Get the app data directory path (for display).
   */
  getAppDataPath: () => ipcRenderer.invoke('wizard:get-appdata-path'),

  /**
   * Signal that wizard is done and the app should start.
   */
  completeWizard: () => ipcRenderer.send('wizard:complete'),

  /**
   * Window controls for frameless window.
   */
  minimizeWindow: () => ipcRenderer.send('window:minimize'),
  closeWindow: () => ipcRenderer.send('window:close'),
});
