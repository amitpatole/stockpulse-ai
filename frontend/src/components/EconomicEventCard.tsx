import React from 'react';
import { EconomicEvent } from '@/hooks/useEconomicEvents';
import { StockImpactBadge } from './StockImpactBadge';
import { format } from 'date-fns';

export interface EconomicEventCardProps {
  event: EconomicEvent;
}

export function EconomicEventCard({ event }: EconomicEventCardProps) {
  const importance_colors = {
    low: 'bg-gray-100 text-gray-800',
    medium: 'bg-yellow-100 text-yellow-800',
    high: 'bg-red-100 text-red-800',
  };

  const importance_class = importance_colors[event.importance as keyof typeof importance_colors];

  const formatted_date = new Date(event.scheduled_date);
  const is_past = formatted_date < new Date();

  return (
    <tr className={`border-t border-gray-200 hover:bg-gray-50 transition-colors ${is_past ? 'opacity-60' : ''}`}>
      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
        {event.event_name}
      </td>
      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
        {event.country}
      </td>
      <td className="px-6 py-4 whitespace-nowrap text-sm">
        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${importance_class}`}>
          {event.importance.charAt(0).toUpperCase() + event.importance.slice(1)}
        </span>
      </td>
      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
        {format(formatted_date, 'MMM dd, yyyy HH:mm')}
      </td>
      <td className="px-6 py-4 text-sm text-gray-500">
        <div className="flex flex-wrap gap-2">
          {event.impacts && event.impacts.length > 0 ? (
            event.impacts.map((impact) => (
              <StockImpactBadge
                key={`${event.id}-${impact.ticker}`}
                ticker={impact.ticker}
                sensitivity_score={impact.sensitivity_score}
              />
            ))
          ) : (
            <span className="text-gray-400 text-xs">No impacts</span>
          )}
        </div>
      </td>
    </tr>
  );
}