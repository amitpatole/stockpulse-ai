'use client';

import DOMPurify from 'dompurify';
import { useState, useMemo } from 'react';
import { FileText, Loader2, Calendar, Bot, Filter, Play } from 'lucide-react';
import { clsx } from 'clsx';
import Header from '@/components/layout/Header';
import { useApi } from '@/hooks/useApi';
import { getResearchBriefs, generateResearchBrief, getStocks } from '@/lib/api';
import type { ResearchBrief, Stock } from '@/lib/types';

function formatDate(dateStr: string): string {
  const date = new Date(dateStr);
  return date.toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#x27;');
}

function MarkdownContent({ content }: { content: string }) {
  // Escape HTML special characters first so that any injected markup in the
  // AI-generated content cannot survive into the rendered output.  The markdown
  // regex transforms below only produce safe, known HTML patterns.
  const escaped = escapeHtml(content);
  const rawHtml = escaped
    .replace(/^### (.+)$/gm, '<h3 class="text-base font-semibold text-white mt-4 mb-2">$1</h3>')
    .replace(/^## (.+)$/gm, '<h2 class="text-lg font-bold text-white mt-5 mb-2">$1</h2>')
    .replace(/^# (.+)$/gm, '<h1 class="text-xl font-bold text-white mt-6 mb-3">$1</h1>')
    .replace(/\*\*(.+?)\*\*/g, '<strong class="font-semibold text-white">$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/^- (.+)$/gm, '<li class="ml-4 list-disc text-slate-300 mb-1">$1</li>')
    .replace(/^(\d+)\. (.+)$/gm, '<li class="ml-4 list-decimal text-slate-300 mb-1">$2</li>')
    .replace(/`(.+?)`/g, '<code class="rounded bg-slate-700 px-1.5 py-0.5 text-xs text-blue-400 font-mono">$1</code>')
    .replace(/\n\n/g, '</p><p class="text-sm text-slate-300 leading-relaxed mb-3">')
    .replace(/\n/g, '<br />');

  // DOMPurify requires a browser DOM — guard for the SSR pass.
  const sanitized = typeof window !== 'undefined' ? DOMPurify.sanitize(rawHtml) : rawHtml;

  return (
    <div
      className="prose prose-invert max-w-none text-sm text-slate-300 leading-relaxed"
      dangerouslySetInnerHTML={{ __html: `<p class="text-sm text-slate-300 leading-relaxed mb-3">${sanitized}</p>` }}
    />
  );
}

export default function ResearchPage() {
  const [selectedBrief, setSelectedBrief] = useState<ResearchBrief | null>(null);
  const [filterTicker, setFilterTicker] = useState('');
  const [generating, setGenerating] = useState(false);
  const [genError, setGenError] = useState<string | null>(null);

  const { data: briefs, loading, error, refetch } = useApi<ResearchBrief[]>(
    () => getResearchBriefs(filterTicker || undefined),
    [filterTicker],
    { refreshInterval: 30000 }
  );

  const { data: stocks } = useApi<Stock[]>(getStocks, []);

  // Get unique tickers from briefs
  const tickers = useMemo(() => {
    if (!briefs) return [];
    const set = new Set(briefs.map((b) => b.ticker));
    return Array.from(set).sort();
  }, [briefs]);

  const handleGenerate = async () => {
    setGenerating(true);
    setGenError(null);
    try {
      const brief = await generateResearchBrief(filterTicker || undefined);
      await refetch();
      setSelectedBrief(brief);
      setGenerating(false);
    } catch (err) {
      setGenError(err instanceof Error ? err.message : 'Failed to generate brief');
      setGenerating(false);
    }
  };

  return (
    <div className="flex flex-col">
      <Header title="Research Briefs" subtitle="AI-generated research analysis" />

      <div className="flex-1 p-6">
        {/* Toolbar */}
        <div className="mb-6 flex flex-wrap items-center gap-3">
          {/* Filter by ticker */}
          <div className="flex items-center gap-2 rounded-lg border border-slate-700 bg-slate-800/50 px-3 py-2">
            <Filter className="h-4 w-4 text-slate-500" />
            <select
              value={filterTicker}
              onChange={(e) => {
                setFilterTicker(e.target.value);
                setSelectedBrief(null);
              }}
              className="bg-transparent text-sm text-slate-300 outline-none"
            >
              <option value="" className="bg-slate-800">All Tickers</option>
              {(stocks || []).map((s) => (
                <option key={s.ticker} value={s.ticker} className="bg-slate-800">
                  {s.ticker}
                </option>
              ))}
              {tickers
                .filter((t) => !(stocks || []).some((s) => s.ticker === t))
                .map((t) => (
                  <option key={t} value={t} className="bg-slate-800">
                    {t}
                  </option>
                ))}
            </select>
          </div>

          {/* Generate New */}
          <button
            onClick={handleGenerate}
            disabled={generating}
            className="flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-700 disabled:opacity-50"
          >
            {generating ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Play className="h-4 w-4" />
            )}
            Generate New Brief
          </button>

          {genError && (
            <span className="text-xs text-red-400">{genError}</span>
          )}
        </div>

        {/* Content */}
        <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
          {/* Briefs List */}
          <div className="xl:col-span-1">
            <div className="rounded-xl border border-slate-700/50 bg-slate-800/50">
              <div className="border-b border-slate-700/50 px-4 py-3">
                <h2 className="text-sm font-semibold text-white">
                  Briefs {briefs ? `(${briefs.length})` : ''}
                </h2>
              </div>

              <div className="max-h-[calc(100vh-280px)] overflow-y-auto">
                {loading && !briefs && (
                  <div className="space-y-3 p-4">
                    {Array.from({ length: 5 }).map((_, i) => (
                      <div key={i} className="h-16 animate-pulse rounded-lg bg-slate-700/30" />
                    ))}
                  </div>
                )}

                {error && !briefs && (
                  <div className="p-4 text-center text-sm text-red-400">{error}</div>
                )}

                {briefs && briefs.length === 0 && (
                  <div className="p-6 text-center">
                    <FileText className="mx-auto h-8 w-8 text-slate-600" />
                    <p className="mt-2 text-sm text-slate-500">No research briefs yet.</p>
                    <p className="text-xs text-slate-600">Run the Researcher agent to generate briefs.</p>
                  </div>
                )}

                {briefs && briefs.length > 0 && (
                  <div className="divide-y divide-slate-700/30">
                    {briefs.map((brief) => (
                      <button
                        key={brief.id}
                        onClick={() => setSelectedBrief(brief)}
                        className={clsx(
                          'w-full px-4 py-3 text-left transition-colors hover:bg-slate-700/20',
                          selectedBrief?.id === brief.id && 'bg-blue-500/10 border-l-2 border-blue-500'
                        )}
                      >
                        <div className="flex items-center gap-2">
                          <span className="rounded bg-slate-700 px-1.5 py-0.5 text-[10px] font-medium text-slate-300">
                            {brief.ticker}
                          </span>
                          <span className="flex items-center gap-1 text-[10px] text-slate-500">
                            <Bot className="h-2.5 w-2.5" />
                            {brief.agent_name}
                          </span>
                        </div>
                        <p className="mt-1 text-sm text-slate-300 line-clamp-2">{brief.title}</p>
                        <div className="mt-1 flex items-center gap-1 text-[10px] text-slate-500">
                          <Calendar className="h-2.5 w-2.5" />
                          {formatDate(brief.created_at)}
                        </div>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Brief Detail */}
          <div className="xl:col-span-2">
            {selectedBrief ? (
              <div className="rounded-xl border border-slate-700/50 bg-slate-800/50 p-6">
                <div className="mb-4 border-b border-slate-700/50 pb-4">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="rounded bg-blue-500/20 px-2 py-0.5 text-xs font-medium text-blue-400">
                      {selectedBrief.ticker}
                    </span>
                    {selectedBrief.model_used && (
                      <span className="rounded bg-slate-700 px-2 py-0.5 text-xs text-slate-400">
                        {selectedBrief.model_used}
                      </span>
                    )}
                  </div>
                  <h2 className="text-lg font-bold text-white">{selectedBrief.title}</h2>
                  <div className="mt-2 flex items-center gap-3 text-xs text-slate-400">
                    <span className="flex items-center gap-1">
                      <Bot className="h-3 w-3" />
                      {selectedBrief.agent_name}
                    </span>
                    <span className="flex items-center gap-1">
                      <Calendar className="h-3 w-3" />
                      {formatDate(selectedBrief.created_at)}
                    </span>
                  </div>
                </div>

                <MarkdownContent content={selectedBrief.content} />
              </div>
            ) : (
              <div className="flex h-full items-center justify-center rounded-xl border border-dashed border-slate-700 bg-slate-800/20 p-12">
                <div className="text-center">
                  <FileText className="mx-auto h-12 w-12 text-slate-700" />
                  <p className="mt-3 text-sm text-slate-500">Select a brief to view its content</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
