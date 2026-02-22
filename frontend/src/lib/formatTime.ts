import type { TimezoneMode } from './types';

const ET_TIMEZONE = 'America/New_York';

function resolveTimezone(mode: TimezoneMode): string {
  return mode === 'ET' ? ET_TIMEZONE : Intl.DateTimeFormat().resolvedOptions().timeZone;
}

/**
 * Format an ISO timestamp as a short time string with timezone label.
 * Returns "—" for null, undefined, or unparseable input.
 * Example output: "14:32 CET" (local) or "09:32 ET" (ET mode)
 */
export function formatTimestamp(iso: string | null | undefined, tz: TimezoneMode): string {
  if (!iso) return '—';
  try {
    const date = new Date(iso);
    if (isNaN(date.getTime())) return '—';
    return new Intl.DateTimeFormat(undefined, {
      timeZone: resolveTimezone(tz),
      hour: '2-digit',
      minute: '2-digit',
      timeZoneName: 'short',
    }).format(date);
  } catch {
    return '—';
  }
}

/**
 * Format an ISO timestamp as a full date+time string with timezone label.
 * Returns "—" for null, undefined, or unparseable input.
 * Example output: "22 Feb 2026, 14:32 CET"
 */
export function formatDate(iso: string | null | undefined, tz: TimezoneMode): string {
  if (!iso) return '—';
  try {
    const date = new Date(iso);
    if (isNaN(date.getTime())) return '—';
    return new Intl.DateTimeFormat(undefined, {
      timeZone: resolveTimezone(tz),
      day: '2-digit',
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
