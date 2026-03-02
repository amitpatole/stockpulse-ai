import React from 'react';

export interface StockImpactBadgeProps {
  ticker: string;
  sensitivity_score: number;
}

export function StockImpactBadge({ ticker, sensitivity_score }: StockImpactBadgeProps) {
  const get_color = (score: number) => {
    if (score >= 8) return 'bg-red-50 text-red-700 border-red-200';
    if (score >= 5) return 'bg-yellow-50 text-yellow-700 border-yellow-200';
    return 'bg-green-50 text-green-700 border-green-200';
  };

  const get_intensity = (score: number) => {
    if (score >= 8) return 'Very High';
    if (score >= 5) return 'Medium';
    return 'Low';
  };

  return (
    <span
      className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium border ${get_color(sensitivity_score)}`}
      title={`${ticker} sensitivity: ${sensitivity_score.toFixed(1)}/10`}
    >
      {ticker} <span className="ml-1 text-[10px] opacity-70">({get_intensity(sensitivity_score)})</span>
    </span>
  );
}