```typescript
'use client';

import React, { useState } from 'react';
import Head from 'next/head';
import { InsiderFilings } from '@/components/insiders/InsiderFilings';
import { InsiderStats } from '@/components/insiders/InsiderStats';

export default function InsiderTradingPage() {
  const [activeTab, setActiveTab] = useState<'activity' | 'stats' | 'about'>('activity');
  const [selectedCik, setSelectedCik] = useState('0000320193'); // Apple as default

  return (
    <>
      <Head>
        <title>Insider Trading Tracker - TickerPulse</title>
        <meta name="description" content="Monitor SEC Form 4 filings for insider trading activity" />
      </Head>

      <div className="space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold text-slate-900">Insider Trading Tracker</h1>
          <p className="text-slate-600 mt-2">
            Monitor SEC Form 4 filings to track insider buying and selling activity across your portfolio.
          </p>
        </div>

        {/* Tabs */}
        <div className="border-b border-slate-200">
          <div className="flex gap-8">
            {(['activity', 'stats', 'about'] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`py-3 px-1 font-medium text-sm border-b-2 transition-colors ${
                  activeTab === tab
                    ? 'border-blue-600 text-blue-600'
                    : 'border-transparent text-slate-600 hover:text-slate-900'
                }`}
              >
                {tab === 'activity' && 'Recent Activity'}
                {tab === 'stats' && 'Statistics'}
                {tab === 'about' && 'About'}
              </button>
            ))}
          </div>
        </div>

        {/* Tab Content */}
        {activeTab === 'activity' && (
          <div>
            <h2 className="text-xl font-semibold text-slate-900 mb-4">Recent Insider Filings</h2>
            <InsiderFilings />
          </div>
        )}

        {activeTab === 'stats' && (
          <div>
            <h2 className="text-xl font-semibold text-slate-900 mb-4">Aggregate Statistics</h2>
            <InsiderStats cik={selectedCik} />
          </div>
        )}

        {activeTab === 'about' && (
          <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-6 space-y-4">
            <h2 className="text-lg font-semibold text-slate-900">About Insider Trading Data</h2>
            <p className="text-slate-700">
              This tracker monitors SEC Form 4 filings, which are filed by corporate officers, directors, and
              beneficial owners when they buy or sell company stock.
            </p>
            <div className="space-y-3">
              <div>
                <p className="font-medium text-slate-900">Sentiment Score</p>
                <p className="text-sm text-slate-600">
                  Buy transactions score +1.0 (bullish), sales score -1.0 (bearish), with other transactions
                  weighted accordingly.
                </p>
              </div>
              <div>
                <p className="font-medium text-slate-900">Data Source</p>
                <p className="text-sm text-slate-600">
                  All data comes from the SEC's EDGAR database and Form 4 filings are updated daily.
                </p>
              </div>
              <div>
                <p className="font-medium text-slate-900">Significance</p>
                <p className="text-sm text-slate-600">
                  While insider trading can signal confidence in a company, it's just one factor in investment
                  analysis and should not be the sole basis for decisions.
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    </>
  );
}
```