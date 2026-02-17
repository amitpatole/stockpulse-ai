import { app } from 'electron';
import * as path from 'path';
import * as fs from 'fs';

/**
 * User data directory: %APPDATA%/TickerPulse/
 * Stores .env, database, logs, and setup flag.
 */
export function getAppDataPath(): string {
  const p = path.join(app.getPath('appData'), 'TickerPulse');
  fs.mkdirSync(p, { recursive: true });
  return p;
}

/**
 * Resolve a path relative to the app's bundled resources.
 * In production: process.resourcesPath (inside the ASAR/extraResources)
 * In development: relative to the project root (tickerpulse-ai/)
 */
export function getResourcePath(relativePath: string): string {
  if (app.isPackaged) {
    return path.join(process.resourcesPath, relativePath);
  }
  // Dev mode: electron/ is one level inside tickerpulse-ai/
  return path.join(__dirname, '..', '..', '..', relativePath);
}

/**
 * Check if this is the first run (no setup-complete.flag).
 */
export function isFirstRun(): boolean {
  const flagPath = path.join(getAppDataPath(), 'setup-complete.flag');
  return !fs.existsSync(flagPath);
}

/**
 * Mark setup as complete by writing a flag file.
 */
export function markSetupComplete(): void {
  const flagPath = path.join(getAppDataPath(), 'setup-complete.flag');
  fs.writeFileSync(flagPath, new Date().toISOString(), 'utf-8');
}

/**
 * Get the path to the .env file in user data.
 */
export function getEnvPath(): string {
  return path.join(getAppDataPath(), '.env');
}

/**
 * Get the path to the logs directory.
 */
export function getLogsPath(): string {
  const p = path.join(getAppDataPath(), 'logs');
  fs.mkdirSync(p, { recursive: true });
  return p;
}
