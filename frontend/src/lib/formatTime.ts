import type { TimezoneMode } from './types';

const ET_TIMEZONE = 'America/New_York';

function resolvedTimeZone(tz: TimezoneMode): string {
  return tz === 'ET' ? ET_TIMEZONE : Intl.DateTimeFormat().resolvedOptions().timeZone;
}

/**
 * Format an ISO timestamp as a short time string with explicit timezone label.
 * Returns "14:32 CET", "09:32 ET", etc. Returns "—" on null/invalid input.
 */
export function formatTimestamp(iso: string | null | undefined, tz: TimezoneMode): string {
  if (iso == null || iso === '') return '—';
  try {
    const date = new Date(iso);
    if (isNaN(date.getTime())) return '—';
    return new Intl.DateTimeFormat(undefined, {
      timeZone: resolvedTimeZone(tz),
      hour: '2-digit',
      minute: '2-digit',
      timeZoneName: 'short',
    }).format(date);
  } catch {
    return '—';
  }
}

/**
 * Format an ISO timestamp as a long date+time string with explicit timezone label.
 * Returns "22 Feb 2026, 14:32 CET", etc. Returns "—" on null/invalid input.
 */
export function formatDate(iso: string | null | undefined, tz: TimezoneMode): string {
  if (iso == null || iso === '') return '—';
  try {
    const date = new Date(iso);
    if (isNaN(date.getTime())) return '—';
    return new Intl.DateTimeFormat(undefined, {
      timeZone: resolvedTimeZone(tz),
      day: 'numeric',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      timeZoneName: 'short',
    }).format(date);
  } catch {
    return '—';
  }
}
