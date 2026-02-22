'use client';

import { useRef, useState } from 'react';
import { Loader2, Plus, X } from 'lucide-react';

const MAX_SYMBOLS = 4;

interface CompareInputProps {
  symbols: string[];
  colors: string[];
  warnings: Record<string, string>;
  onAdd: (symbol: string) => void;
  onRemove: (symbol: string) => void;
  loading?: boolean;
}

export default function CompareInput({
  symbols,
  colors,
  warnings,
  onAdd,
  onRemove,
  loading = false,
}: CompareInputProps) {
  const [inputValue, setInputValue] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);

  const canAdd = symbols.length < MAX_SYMBOLS;

  function handleAdd() {
    const sym = inputValue.trim().toUpperCase();
    if (!sym || symbols.includes(sym)) {
      setInputValue('');
      return;
    }
    onAdd(sym);
    setInputValue('');
    inputRef.current?.focus();
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleAdd();
    }
  }

  return (
    <div className="mt-3 space-y-2">
      {/* Symbol chips */}
      {symbols.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {symbols.map((symbol, idx) => {
            const color = colors[idx] ?? '#f59e0b';
            const warning = warnings[symbol];
            return (
              <div key={symbol} className="flex flex-col gap-0.5">
                <div className="flex items-center gap-1.5 rounded-full border border-slate-700 bg-slate-800 px-3 py-1">
                  <span
                    className="inline-block h-2 w-2 flex-shrink-0 rounded-full"
                    style={{ backgroundColor: color }}
                  />
                  <span className="text-xs font-semibold text-white">{symbol}</span>
                  <button
                    onClick={() => onRemove(symbol)}
                    aria-label={`Remove ${symbol}`}
                    className="ml-0.5 text-slate-500 transition-colors hover:text-white"
                  >
                    <X className="h-3 w-3" />
                  </button>
                </div>
                {warning && (
                  <p className="pl-2 text-[10px] text-red-400">
                    {symbol}: {warning}
                  </p>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Input row */}
      <div className="flex items-center gap-2">
        <div className="flex items-center gap-1.5 rounded-lg border border-slate-700 bg-slate-800 px-3 py-1.5 focus-within:border-blue-500/50 focus-within:ring-1 focus-within:ring-blue-500/30">
          <input
            ref={inputRef}
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={canAdd ? 'Add symbol (max 4)' : 'Max 4 symbols'}
            disabled={!canAdd}
            className="w-36 bg-transparent text-xs text-white placeholder-slate-500 focus:outline-none disabled:cursor-not-allowed disabled:opacity-50"
            aria-label="Add comparison symbol"
          />
        </div>
        <button
          onClick={handleAdd}
          disabled={!canAdd || !inputValue.trim()}
          aria-label="Add symbol"
          className="flex items-center justify-center rounded-lg border border-slate-700 bg-slate-800 p-1.5 text-slate-400 transition-colors hover:bg-slate-700 hover:text-white disabled:cursor-not-allowed disabled:opacity-40"
        >
          <Plus className="h-3.5 w-3.5" />
        </button>
        {loading && (
          <Loader2
            className="h-3.5 w-3.5 animate-spin text-slate-400"
            aria-hidden="true"
          />
        )}
      </div>
    </div>
  );
}
