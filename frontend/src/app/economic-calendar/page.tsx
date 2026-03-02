'use client';

import Header from '@/components/layout/Header';
import { useEconomicEvents } from '@/hooks/useEconomicEvents';
import { EconomicCalendarTable } from '@/components/EconomicCalendarTable';

export default function EconomicCalendarPage() {
  const {
    events,
    meta,
    loading,
    error,
    setStartDate,
    setEndDate,
    setCountry,
    setImportance,
    setLimit,
    setOffset,
  } = useEconomicEvents();

  return (
    <div className="flex flex-col">
      <Header
        title="Economic Calendar"
        subtitle="Track upcoming economic events and their potential impact on your monitored stocks"
      />

      <div className="flex-1 p-6">
        <EconomicCalendarTable
          events={events}
          meta={meta}
          loading={loading}
          error={error}
          onFilterChange={{
            startDate: setStartDate,
            endDate: setEndDate,
            country: setCountry,
            importance: setImportance,
          }}
          onPaginate={{
            setLimit,
            setOffset,
          }}
        />
      </div>
    </div>
  );
}