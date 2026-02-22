'use client';

import { useSSE } from '@/hooks/useSSE';

export default function SSEAccessibilityAnnouncer() {
  const { announcement } = useSSE();

  return (
    <>
      <div className="sr-only" aria-live="assertive" aria-atomic="true">
        {announcement.assertive}
      </div>
      <div className="sr-only" aria-live="polite" aria-atomic="true">
        {announcement.polite}
      </div>
    </>
  );
}
