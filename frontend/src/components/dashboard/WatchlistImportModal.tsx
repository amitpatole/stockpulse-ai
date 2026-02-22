'use client';

import { useEffect, useRef, useState } from 'react';
import { X, Upload, Loader2, CheckCircle, AlertTriangle } from 'lucide-react';
import { importWatchlistCsv, ApiError } from '@/lib/api';
import type { WatchlistImportResult } from '@/lib/types';

interface Props {
  watchlistId: number;
  onClose: () => void;
  onImported: () => void;
  triggerRef: React.RefObject<HTMLButtonElement | null>;
}

export default function WatchlistImportModal({
  watchlistId,
  onClose,
  onImported,
  triggerRef,
}: Props) {
  const dialogRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const headingId = 'watchlist-import-dlg';

  const [file, setFile] = useState<File | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<WatchlistImportResult | null>(null);
  const [isDragging, setIsDragging] = useState(false);

  // Focus trap & keyboard handling
  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;

    const selectors =
      'button:not([disabled]), [href], input:not([disabled]), [tabindex]:not([tabindex="-1"])';
    const elements = Array.from(dialog.querySelectorAll<HTMLElement>(selectors));
    elements[0]?.focus();

    function onKeyDown(e: KeyboardEvent) {
      if (e.key === 'Escape') {
        onClose();
        return;
      }
      if (e.key !== 'Tab' || elements.length === 0) return;
      const first = elements[0];
      const last = elements[elements.length - 1];
      if (e.shiftKey) {
        if (document.activeElement === first) {
          e.preventDefault();
          last.focus();
        }
      } else {
        if (document.activeElement === last) {
          e.preventDefault();
          first.focus();
        }
      }
    }

    document.addEventListener('keydown', onKeyDown);
    return () => {
      document.removeEventListener('keydown', onKeyDown);
      triggerRef.current?.focus();
    };
  }, [onClose, triggerRef]);

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const selected = e.target.files?.[0] ?? null;
    setFile(selected);
    setError(null);
    setResult(null);
  }

  function handleDrop(e: React.DragEvent) {
    e.preventDefault();
    setIsDragging(false);
    const dropped = e.dataTransfer.files?.[0];
    if (dropped) {
      setFile(dropped);
      setError(null);
      setResult(null);
    }
  }

  async function handleImport() {
    if (!file) {
      setError('Please select a CSV file first');
      return;
    }
    setIsLoading(true);
    setError(null);
    setResult(null);
    try {
      const data = await importWatchlistCsv(watchlistId, file);
      setResult(data);
      if (data.added > 0) {
        onImported();
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Import failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  }

  const hasResult = result !== null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby={headingId}
        className="relative w-full max-w-md rounded-xl border border-slate-700 bg-slate-900 p-6 shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="mb-5 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Upload className="h-5 w-5 text-blue-400" aria-hidden="true" />
            <h2 id={headingId} className="text-lg font-semibold text-white">
              Import from CSV
            </h2>
          </div>
          <button
            onClick={onClose}
            className="rounded-lg p-1 text-slate-400 transition-colors hover:bg-slate-800 hover:text-white"
            aria-label="Close import dialog"
          >
            <X className="h-5 w-5" aria-hidden="true" />
          </button>
        </div>

        {/* Drop zone */}
        {!hasResult && (
          <>
            <div
              role="button"
              tabIndex={0}
              aria-label="Drop zone for CSV file. Click or drop a file here."
              className={`mb-4 flex cursor-pointer flex-col items-center justify-center gap-2 rounded-lg border-2 border-dashed px-4 py-8 text-center transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500/50 ${
                isDragging
                  ? 'border-blue-500 bg-blue-500/10'
                  : 'border-slate-600 bg-slate-800/40 hover:border-slate-500 hover:bg-slate-800/60'
              }`}
              onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
              onDragLeave={() => setIsDragging(false)}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') fileInputRef.current?.click(); }}
            >
              <Upload className="h-8 w-8 text-slate-500" aria-hidden="true" />
              {file ? (
                <p className="text-sm font-medium text-blue-400">{file.name}</p>
              ) : (
                <>
                  <p className="text-sm text-slate-300">
                    Drop a CSV file here, or{' '}
                    <span className="text-blue-400 underline">browse</span>
                  </p>
                  <p className="text-xs text-slate-500">
                    Must have a <code className="rounded bg-slate-700 px-1">symbol</code> column
                    &mdash; max 500 rows, 1 MB
                  </p>
                </>
              )}
            </div>
            <input
              ref={fileInputRef}
              type="file"
              accept=".csv"
              className="sr-only"
              aria-hidden="true"
              tabIndex={-1}
              onChange={handleFileChange}
            />
          </>
        )}

        {/* Error banner */}
        {error && (
          <div
            role="alert"
            className="mb-4 flex items-start gap-2 rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-400"
          >
            <AlertTriangle className="mt-0.5 h-4 w-4 flex-shrink-0" aria-hidden="true" />
            <span>{error}</span>
          </div>
        )}

        {/* Result summary */}
        {hasResult && result && (
          <div className="mb-5 rounded-lg border border-slate-700 bg-slate-800/50 p-4">
            <div className="mb-3 flex items-center gap-2">
              <CheckCircle className="h-5 w-5 text-emerald-400" aria-hidden="true" />
              <p className="font-medium text-white">Import complete</p>
            </div>
            <ul className="space-y-1 text-sm">
              <li className="flex justify-between">
                <span className="text-slate-400">Added</span>
                <span className="font-semibold text-emerald-400">{result.added}</span>
              </li>
              <li className="flex justify-between">
                <span className="text-slate-400">Duplicates skipped</span>
                <span className="font-semibold text-slate-300">{result.skipped_duplicates}</span>
              </li>
              <li className="flex justify-between">
                <span className="text-slate-400">Invalid symbols</span>
                <span className="font-semibold text-amber-400">{result.skipped_invalid}</span>
              </li>
            </ul>
            {result.invalid_symbols.length > 0 && (
              <div className="mt-3">
                <p className="mb-1.5 text-xs text-slate-400">Unrecognised symbols:</p>
                <div className="flex flex-wrap gap-1.5">
                  {result.invalid_symbols.map((sym) => (
                    <span
                      key={sym}
                      className="rounded bg-amber-500/20 px-2 py-0.5 text-xs font-medium text-amber-400"
                    >
                      {sym}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Actions */}
        <div className="flex justify-end gap-3">
          <button
            onClick={onClose}
            className="rounded-lg border border-slate-700 px-4 py-2 text-sm text-slate-300 transition-colors hover:bg-slate-800 hover:text-white"
          >
            {hasResult ? 'Close' : 'Cancel'}
          </button>
          {!hasResult && (
            <button
              onClick={handleImport}
              disabled={isLoading || !file}
              className="flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {isLoading ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
                  Importing…
                </>
              ) : (
                <>
                  <Upload className="h-4 w-4" aria-hidden="true" />
                  Import
                </>
              )}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
