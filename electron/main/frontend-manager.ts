import { spawn, ChildProcess } from 'child_process';
import * as http from 'http';
import log from 'electron-log';
import { getResourcePath } from './paths';

export class FrontendManager {
  private process: ChildProcess | null = null;
  private port = 3000;

  /**
   * Start the Next.js frontend server.
   */
  async start(): Promise<void> {
    const { existsSync } = await import('fs');

    let exePath: string;
    let args: string[];
    let cwd: string;

    const packagedNode = getResourcePath('frontend/node.exe');
    const packagedServer = getResourcePath('frontend/server.js');

    if (existsSync(packagedNode) && existsSync(packagedServer)) {
      // Production: bundled Node.js + standalone server
      exePath = packagedNode;
      args = [packagedServer];
      cwd = getResourcePath('frontend');
      log.info(`Starting frontend (packaged): ${exePath} server.js`);
    } else {
      // Dev mode: use system npm
      exePath = process.platform === 'win32' ? 'npm.cmd' : 'npm';
      args = ['run', 'start'];
      cwd = getResourcePath('frontend');
      log.info(`Starting frontend (dev): npm run start`);
    }

    const env: Record<string, string> = {
      ...process.env as Record<string, string>,
      PORT: String(this.port),
      HOSTNAME: 'localhost',
      NODE_ENV: 'production',
    };

    this.process = spawn(exePath, args, {
      cwd,
      env,
      stdio: ['ignore', 'pipe', 'pipe'],
      windowsHide: true,
    });

    this.process.stdout?.on('data', (data: Buffer) => {
      log.info(`[frontend] ${data.toString().trim()}`);
    });

    this.process.stderr?.on('data', (data: Buffer) => {
      log.warn(`[frontend] ${data.toString().trim()}`);
    });

    this.process.on('exit', (code) => {
      log.info(`Frontend exited with code ${code}`);
    });
  }

  /**
   * Wait for the frontend to be ready.
   */
  async waitForReady(timeoutMs = 20000): Promise<void> {
    const start = Date.now();
    while (Date.now() - start < timeoutMs) {
      try {
        const ready = await this.checkReady();
        if (ready) {
          log.info('Frontend ready');
          return;
        }
      } catch {
        // retry
      }
      await new Promise((r) => setTimeout(r, 500));
    }
    throw new Error('Frontend failed to start within timeout');
  }

  private checkReady(): Promise<boolean> {
    return new Promise((resolve) => {
      http
        .get(`http://localhost:${this.port}`, (res) => {
          resolve(res.statusCode === 200 || res.statusCode === 304);
        })
        .on('error', () => resolve(false));
    });
  }

  /**
   * Stop the frontend process.
   */
  async stop(): Promise<void> {
    if (this.process && !this.process.killed) {
      if (process.platform === 'win32') {
        spawn('taskkill', ['/pid', String(this.process.pid), '/f', '/t'], {
          windowsHide: true,
        });
      } else {
        this.process.kill('SIGTERM');
      }
      this.process = null;
      log.info('Frontend stopped');
    }
  }
}
