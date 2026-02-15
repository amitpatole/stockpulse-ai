import { ipcMain } from 'electron';
import log from 'electron-log';
import { writeEnvFile, WizardConfig } from './env-manager';
import { markSetupComplete, getAppDataPath } from './paths';

export function registerIpcHandlers(): void {
  /**
   * Test an AI provider API key directly (backend not running during wizard).
   */
  ipcMain.handle(
    'wizard:test-ai-provider',
    async (
      _event,
      args: { provider: string; api_key: string }
    ): Promise<{ success: boolean; error?: string }> => {
      return testProviderDirect(args.provider, args.api_key);
    }
  );

  /**
   * Save wizard configuration to .env and mark setup complete.
   */
  ipcMain.handle(
    'wizard:save-config',
    async (_event, config: WizardConfig): Promise<{ success: boolean; error?: string }> => {
      try {
        writeEnvFile(config);
        markSetupComplete();
        log.info('Wizard configuration saved');
        return { success: true };
      } catch (err) {
        log.error('Failed to save wizard config:', err);
        return { success: false, error: String(err) };
      }
    }
  );

  /**
   * Return the app data path for display in wizard.
   */
  ipcMain.handle('wizard:get-appdata-path', async () => {
    return getAppDataPath();
  });
}

/**
 * Test an AI provider's API key with a lightweight request.
 */
async function testProviderDirect(
  provider: string,
  apiKey: string
): Promise<{ success: boolean; error?: string }> {
  if (!apiKey || apiKey.trim().length === 0) {
    return { success: false, error: 'API key is empty' };
  }

  const tests: Record<string, () => Promise<Response>> = {
    anthropic: () =>
      fetch('https://api.anthropic.com/v1/messages', {
        method: 'POST',
        headers: {
          'x-api-key': apiKey,
          'anthropic-version': '2023-06-01',
          'content-type': 'application/json',
        },
        body: JSON.stringify({
          model: 'claude-haiku-4-5-20251001',
          max_tokens: 1,
          messages: [{ role: 'user', content: 'test' }],
        }),
      }),
    openai: () =>
      fetch('https://api.openai.com/v1/models', {
        headers: { Authorization: `Bearer ${apiKey}` },
      }),
    google: () =>
      fetch(
        `https://generativelanguage.googleapis.com/v1beta/models?key=${apiKey}`
      ),
    xai: () =>
      fetch('https://api.x.ai/v1/models', {
        headers: { Authorization: `Bearer ${apiKey}` },
      }),
  };

  const testFn = tests[provider];
  if (!testFn) {
    return { success: false, error: `Unknown provider: ${provider}` };
  }

  try {
    const result = await testFn();
    if (result.ok) {
      return { success: true };
    }
    if (result.status === 401 || result.status === 403) {
      return { success: false, error: 'Invalid API key' };
    }
    return { success: false, error: `HTTP ${result.status}` };
  } catch (err) {
    return { success: false, error: `Connection failed: ${String(err)}` };
  }
}
