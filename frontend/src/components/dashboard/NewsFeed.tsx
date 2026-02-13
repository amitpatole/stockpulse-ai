'use client';

import { ExternalLink, Clock } from 'lucide-react';
import { clsx } from 'clsx';
import { useApi } from '@/hooks/useApi';
import { getNews } from '@/lib/api';
import type { NewsArticle } from '@/lib/types';
import { SENTIMENT_COLORS } from '@/lib/types';

function timeAgo(dateStr: string): string {
  const now = new Date();
  const date = new Date(dateStr);
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);

  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  const diffHours = Math.floor(diffMins / 60);
  if (diffHours < 24) return `${diffHours}h ago`;
  const diffDays = Math.floor(diffHours / 24);
  return `${diffDays}d ago`;
}

export default function NewsFeed() {
  const { data: articles, loading, error } = useApi<NewsArticle[]>(
    () => getNews(undefined, 20),
    [],
    { refreshInterval: 60000 }
  );

  return (
    <div className="rounded-xl border border-slate-700/50 bg-slate-800/50">
      <div className="border-b border-slate-700/50 px-4 py-3">
        <h2 className="text-sm font-semibold text-white">Recent News</h2>
      </div>

      <div className="max-h-[600px] overflow-y-auto">
        {/* Loading */}
        {loading && !articles && (
          <div className="space-y-3 p-4">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="animate-pulse space-y-2">
                <div className="h-3 w-3/4 rounded bg-slate-700" />
                <div className="h-2 w-1/2 rounded bg-slate-700" />
              </div>
            ))}
          </div>
        )}

        {/* Error */}
        {error && !articles && (
          <div className="p-4 text-center text-sm text-red-400">{error}</div>
        )}

        {/* Articles */}
        {articles && articles.length === 0 && (
          <div className="p-6 text-center text-sm text-slate-500">No news articles yet.</div>
        )}

        {articles && articles.length > 0 && (
          <div className="divide-y divide-slate-700/30">
            {articles.map((article) => (
              <div key={article.id} className="px-4 py-3 transition-colors hover:bg-slate-700/20">
                <div className="flex items-start gap-2">
                  <div className="flex-1 min-w-0">
                    <a
                      href={article.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="group flex items-start gap-1"
                    >
                      <p className="text-sm text-slate-200 line-clamp-2 group-hover:text-blue-400 transition-colors">
                        {article.title}
                      </p>
                      <ExternalLink className="mt-0.5 h-3 w-3 flex-shrink-0 text-slate-600 group-hover:text-blue-400" />
                    </a>

                    <div className="mt-1.5 flex items-center gap-2 flex-wrap">
                      {/* Ticker badge */}
                      <span className="rounded bg-slate-700 px-1.5 py-0.5 text-[10px] font-medium text-slate-300">
                        {article.ticker}
                      </span>

                      {/* Sentiment badge */}
                      <span
                        className={clsx(
                          'rounded px-1.5 py-0.5 text-[10px] font-medium',
                          SENTIMENT_COLORS[article.sentiment_label] || 'bg-slate-500/20 text-slate-400'
                        )}
                      >
                        {article.sentiment_label}
                      </span>

                      {/* Source */}
                      <span className="text-[10px] text-slate-500">{article.source}</span>

                      {/* Time */}
                      <span className="flex items-center gap-0.5 text-[10px] text-slate-500">
                        <Clock className="h-2.5 w-2.5" />
                        {timeAgo(article.created_at)}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
