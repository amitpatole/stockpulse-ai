import { spawn, ChildProcess } from 'child_process';
import * as path from 'path';
import * as http from 'http';
import log from 'electron-log';
import { getResourcePath, getAppDataPath, getEnvPath, getLogsPath } from './paths';
import { parseEnvFile } from './env-manager';

export class BackendManager {
  private process: ChildProcess | null = null;
  private port = 5000;

  /**
   * Start the backend process (PyInstaller exe or dev Python).
   */
  async start(): Promise<void> {
    const appDataDir = getAppDataPath();
    const envPath = getEnvPath();
    const logsDir = getLogsPath();

    // Environment variables for the backend
    const env: Record<string, string> = {
      ...process.env as Record<string, string>,
      DB_PATH: path.join(appDataDir, 'stock_news.db'),
      LOG_DIR: logsDir,
      FLASK_PORT: String(this.port),
      FLASK_DEBUG: 'false',
      // Load .env file contents as env vars
      ...parseEnvFile(envPath),
    };

    let exePath: string;
    let args: string[];

    // Detect if running packaged (PyInstaller exe) or dev mode
    const packagedBackend = getResourcePath('backend/stockpulse-backend.exe');
    const { existsSync } = await import('fs');

    if (existsSync(packagedBackend)) {
      // Production: use PyInstaller bundle
      exePath = packagedBackend;
      args = [];
      log.info(`Starting backend (packaged): ${exePath}`);
    } else {
      // Dev mode: use system Python
      exePath = process.platform === 'win32' ? 'python' : 'python3';
      args = ['-m', 'backend.app'];
      env['PYTHONPATH'] = getResourcePath('.');
      log.info(`Starting backend (dev): ${exePath} ${args.join(' ')}`);
    }

    this.process = spawn(exePath, args, {
      cwd: getResourcePath('.'),
      env,
      stdio: ['ignore', 'pipe', 'pipe'],
      windowsHide: true,
    });

    this.process.stdout?.on('data', (data: Buffer) => {
      log.info(`[backend] ${data.toString().trim()}`);
    });

    this.process.stderr?.on('data', (data: Buffer) => {
      log.warn(`[backend] ${data.toString().trim()}`);
    });

    this.process.on('exit', (code) => {
      log.info(`Backend exited with code ${code}`);
    });
  }

  /**
   * Wait for the backend to respond to health checks.
   */
  async waitForHealth(timeoutMs = 30000): Promise<void> {
    const start = Date.now();
    while (Date.now() - start < timeoutMs) {
      try {
        const healthy = await this.checkHealth();
        if (healthy) {
          log.info('Backend health check passed');
          return;
        }
      } catch {
        // retry
      }
      await new Promise((r) => setTimeout(r, 500));
    }
    throw new Error('Backend failed to start within timeout');
  }

  private checkHealth(): Promise<boolean> {
    return new Promise((resolve) => {
      http
        .get(`http://localhost:${this.port}/api/health`, (res) => {
          resolve(res.statusCode === 200);
        })
        .on('error', () => resolve(false));
    });
  }

  /**
   * Stop the backend process and its children.
   */
  async stop(): Promise<void> {
    if (this.process && !this.process.killed) {
      if (process.platform === 'win32') {
        // Windows: taskkill to kill the process tree
        spawn('taskkill', ['/pid', String(this.process.pid), '/f', '/t'], {
          windowsHide: true,
        });
      } else {
        this.process.kill('SIGTERM');
      }
      this.process = null;
      log.info('Backend stopped');
    }
  }
}
