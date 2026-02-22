'use client';

import { useEffect, useRef, useState } from 'react';
import { X, Upload, Loader2, CheckCircle, AlertTriangle } from 'lucide-react';
import { importWatchlistCsv, ApiError } from '@/lib/api';
import type { WatchlistImportResult } from '@/lib/types';

interface Props {
  watchlistId: number;
  onClose: () => void;
  onImported: () => void;
}

export default function WatchlistImportModal({ watchlistId, onClose, onImported }: Props) {
  const dialogRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const headingId = 'import-csv-heading';

  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<WatchlistImportResult | null>(null);

  // Focus trap
  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;

    const selectors =
      'button:not([disabled]), input:not([disabled]), [tabindex]:not([tabindex="-1"])';
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
    return () => document.removeEventListener('keydown', onKeyDown);
  }, [onClose]);

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0] ?? null;
    setSelectedFile(file);
    setError(null);
    setResult(null);
  }

  function handleDrop(e: React.DragEvent<HTMLDivElement>) {
    e.preventDefault();
    const file = e.dataTransfer.files?.[0] ?? null;
    if (file) {
      setSelectedFile(file);
      setError(null);
      setResult(null);
    }
  }

  function handleDragOver(e: React.DragEvent<HTMLDivElement>) {
    e.preventDefault();
  }

  async function handleImport() {
    if (!selectedFile) {
      setError('Please select a CSV file first.');
      return;
    }
    setIsLoading(true);
    setError(null);
    setResult(null);
    try {
      const data = await importWatchlistCsv(watchlistId, selectedFile);
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
              Import CSV
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

        {/* Instructions */}
        {!hasResult && (
          <p className="mb-4 text-sm text-slate-400">
            Upload a <span className="text-white">.csv</span> file with a{' '}
            <span className="font-mono text-white">symbol</span> column. Up to 500 rows,
            max 1 MB.
          </p>
        )}

        {/* Drop zone */}
        {!hasResult && (
          <div
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            onClick={() => fileInputRef.current?.click()}
            className="mb-4 flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed border-slate-600 bg-slate-800/40 px-4 py-8 transition-colors hover:border-blue-500/60 hover:bg-slate-800/70"
            role="button"
            tabIndex={0}
            aria-label="Click or drag a CSV file here"
            onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') fileInputRef.current?.click(); }}
          >
            <Upload className="mb-2 h-8 w-8 text-slate-500" aria-hidden="true" />
            {selectedFile ? (
              <p className="text-sm font-medium text-white">{selectedFile.name}</p>
            ) : (
              <>
                <p className="text-sm text-slate-400">Drag & drop or click to select</p>
                <p className="mt-1 text-xs text-slate-500">CSV files only</p>
              </>
            )}
          </div>
        )}

        <input
          ref={fileInputRef}
          type="file"
          accept=".csv"
          className="sr-only"
          onChange={handleFileChange}
          tabIndex={-1}
          aria-hidden="true"
        />

        {/* Error */}
        {error && (
          <div className="mb-4 flex items-start gap-2 rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-400">
            <AlertTriangle className="mt-0.5 h-4 w-4 flex-shrink-0" aria-hidden="true" />
            <span>{error}</span>
          </div>
        )}

        {/* Result summary */}
        {hasResult && result && (
          <div className="mb-5 space-y-3">
            <div className="flex items-center gap-2">
              <CheckCircle className="h-5 w-5 text-emerald-400" aria-hidden="true" />
              <span className="font-medium text-white">Import complete</span>
            </div>

            <div className="rounded-lg border border-slate-700 bg-slate-800/50 px-4 py-3 text-sm">
              <div className="flex justify-between py-1">
                <span className="text-slate-400">Added</span>
                <span className="font-semibold text-emerald-400">{result.added}</span>
              </div>
              <div className="flex justify-between py-1">
                <span className="text-slate-400">Duplicates skipped</span>
                <span className="font-semibold text-slate-300">{result.skipped_duplicates}</span>
              </div>
              <div className="flex justify-between py-1">
                <span className="text-slate-400">Invalid skipped</span>
                <span className="font-semibold text-amber-400">{result.skipped_invalid}</span>
              </div>
            </div>

            {result.invalid_symbols.length > 0 && (
              <div>
                <p className="mb-1.5 text-xs text-slate-500">Unrecognised symbols:</p>
                <div className="flex flex-wrap gap-1.5">
                  {result.invalid_symbols.map((sym) => (
                    <span
                      key={sym}
                      className="rounded bg-amber-500/20 px-2 py-0.5 font-mono text-xs text-amber-400"
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
              disabled={isLoading || !selectedFile}
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
