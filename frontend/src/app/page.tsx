'use client';

import Header from '@/components/layout/Header';
import KPICards from '@/components/dashboard/KPICards';
import StockGrid from '@/components/dashboard/StockGrid';
import NewsFeed from '@/components/dashboard/NewsFeed';
import EarningsCalendar from '@/components/dashboard/EarningsCalendar';
import ProviderRateLimitPanel from '@/components/dashboard/ProviderRateLimitPanel';

export default function DashboardPage() {
  return (
    <div className="flex flex-col">
      <Header title="Dashboard" subtitle="Market overview and stock watchlist" />

      <div className="flex-1 p-6">
        {/* KPI Cards Row */}
        <KPICards />

        {/* API Rate Limit Indicator */}
        <div className="mt-6">
          <ProviderRateLimitPanel />
        </div>

        {/* Main Content: Stock Grid + News Feed + Earnings */}
        <div className="mt-6 grid grid-cols-1 gap-6 xl:grid-cols-3">
          {/* Stock Grid - Takes up 2 columns on xl */}
          <div className="xl:col-span-2">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-sm font-semibold text-white">Stock Watchlist</h2>
            </div>
            <StockGrid />
          </div>

          {/* Right sidebar: News Feed + Earnings Calendar */}
          <div className="xl:col-span-1 flex flex-col gap-6">
            <NewsFeed />
            <EarningsCalendar />
          </div>
        </div>
      </div>
    </div>
  );
}
