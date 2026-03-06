/**
 * Authentication token management for TickerPulse AI
 * Handles extraction, storage, and retrieval of JWT tokens
 */

const AUTH_TOKEN_KEY = 'auth_token';

/**
 * Extract auth token from localStorage
 */
export function getAuthToken(): string | null {
  if (typeof window === 'undefined') {
    return null; // Server-side rendering
  }
  return localStorage.getItem(AUTH_TOKEN_KEY);
}

/**
 * Store auth token in localStorage
 */
export function setAuthToken(token: string): void {
  if (typeof window === 'undefined') return;
  localStorage.setItem(AUTH_TOKEN_KEY, token);
}

/**
 * Remove auth token from localStorage
 */
export function clearAuthToken(): void {
  if (typeof window === 'undefined') return;
  localStorage.removeItem(AUTH_TOKEN_KEY);
}

/**
 * Check if auth token exists
 */
export function hasAuthToken(): boolean {
  return getAuthToken() !== null;
}
