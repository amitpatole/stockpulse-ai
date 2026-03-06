'use client';

import { useState, useEffect } from 'react';
import { ArrowLeft, Loader2, AlertCircle, Bot, Calendar } from 'lucide-react';
import Link from 'next/link';
import { useApi } from '@/hooks/useApi';
import { getResearchBriefDetail } from '@/lib/api';
import type { ResearchBriefDetail as ResearchBriefDetailType } from '@/lib/types';
import MetricsDisplay from './MetricsDisplay';
import ExportButton from './ExportButton';
import MarkdownContent from './MarkdownContent';

interface ResearchBriefDetailProps {
  briefId: number;
}

export default function ResearchBriefDetail({ briefId }: ResearchBriefDetailProps) {
  const { data: brief, loading, error } = useApi<ResearchBriefDetailType>(
    () => getResearchBriefDetail(briefId),
    [briefId]
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <Loader2 className="mx-auto h-8 w-8 animate-spin text-blue-500" />
          <p className="mt-3 text-sm text-slate-400">Loading brief details...</p>
        </div>
      </div>
    );
  }

  if (error || !brief) {
    return (
      <div className="flex items-center gap-3 rounded-lg border border-red-500/30 bg-red-500/10 p-4">
        <AlertCircle className="h-5 w-5 text-red-400 flex-shrink-0" />
        <div>
          <p className="text-sm font-medium text-red-400">Failed to load brief</p>
          <p className="text-xs text-red-400/80">{error || 'Unknown error'}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="border-b border-slate-700/50 pb-4">
        <Link
          href="/research"
          className="inline-flex items-center gap-2 text-xs font-medium text-blue-400 hover:text-blue-300 transition-colors mb-4"
        >
          <ArrowLeft className="h-3 w-3" />
          Back to Briefs
        </Link>

        <div className="space-y-3">
          <div className="flex flex-wrap items-center gap-2">
            <span className="rounded-lg bg-blue-500/20 px-2.5 py-1 text-xs font-semibold text-blue-400 border border-blue-500/30">
              {brief.ticker}
            </span>
            {brief.model_used && (
              <span className="rounded-lg bg-slate-700/50 px-2.5 py-1 text-xs font-medium text-slate-400 border border-slate-600/50">
                {brief.model_used}
              </span>
            )}
          </div>

          <h1 className="text-2xl font-bold text-white">{brief.title}</h1>

          <div className="flex flex-wrap items-center gap-4 text-xs text-slate-400">
            {brief.agent_name && (
              <span className="flex items-center gap-1">
                <Bot className="h-3 w-3" />
                {brief.agent_name}
              </span>
            )}
            <span className="flex items-center gap-1">
              <Calendar className="h-3 w-3" />
              {new Date(brief.created_at).toLocaleDateString(undefined, {
                year: 'numeric',
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit',
              })}
            </span>
          </div>
        </div>
      </div>

      {/* Executive Summary */}
      {brief.executive_summary && (
        <div className="rounded-lg border border-blue-500/20 bg-blue-500/5 p-4">
          <h2 className="mb-2 text-sm font-semibold text-blue-400">Executive Summary</h2>
          <p className="text-sm leading-relaxed text-slate-300">{brief.executive_summary}</p>
        </div>
      )}

      {/* Main Content Area */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Left: Metrics */}
        <div className="lg:col-span-1">
          <div className="rounded-lg border border-slate-700/50 bg-slate-800/50 p-4 sticky top-20">
            <h2 className="mb-4 text-sm font-semibold text-white">Key Metrics</h2>
            <MetricsDisplay metrics={brief.metrics} ticker={brief.ticker} />

            <div className="mt-4 pt-4 border-t border-slate-700/50">
              <ExportButton
                briefId={brief.id}
                briefTitle={brief.title}
                ticker={brief.ticker}
              />
            </div>
          </div>
        </div>

        {/* Right: Content */}
        <div className="lg:col-span-2">
          <div className="rounded-lg border border-slate-700/50 bg-slate-800/50 p-6">
            <h2 className="mb-4 text-lg font-semibold text-white">Research Content</h2>
            <MarkdownContent content={brief.content} />
          </div>
        </div>
      </div>
    </div>
  );
}
