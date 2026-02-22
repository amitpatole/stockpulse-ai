'use client';

import { useEffect, useRef, useState } from 'react';
import { X, Upload, FileText, AlertCircle, CheckCircle2 } from 'lucide-react';
import { importWatchlistCsv, ApiError } from '@/lib/api';
import type { WatchlistImportResult } from '@/lib/types';

interface Props {
  watchlistId: number;
  onClose: () => void;
  onSuccess: () => void;
  triggerRef: React.RefObject<HTMLButtonElement | null>;
}

export default function WatchlistImportModal({ watchlistId, onClose, onSuccess, triggerRef }: Props) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<WatchlistImportResult | null>(null);
  const [isDragOver, setIsDragOver] = useState(false);

  const dialogRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const headingId = 'import-csv-dlg-heading';

  // Focus trap + Escape key
  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;

    const selectors = 'button:not([disabled]), [href], input:not([disabled]), [tabindex]:not([tabindex="-1"])';
    const getFocusable = () => Array.from(dialog.querySelectorAll<HTMLElement>(selectors));

    getFocusable()[0]?.focus();

    function onKeyDown(e: KeyboardEvent) {
      if (e.key === 'Escape') {
        onClose();
        return;
      }
      if (e.key !== 'Tab') return;
      const elements = getFocusable();
      if (elements.length === 0) return;
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

  function handleFileChange(file: File | null) {
    if (!file) return;
    setError(null);
    setResult(null);
    if (!file.name.toLowerCase().endsWith('.csv')) {
      setError('Unsupported file type. Please select a .csv file.');
      return;
    }
    if (file.size > 1 * 1024 * 1024) {
      setError('File is too large. Maximum size is 1 MB.');
      return;
    }
    setSelectedFile(file);
  }

  function handleInputChange(e: React.ChangeEvent<HTMLInputElement>) {
    handleFileChange(e.target.files?.[0] ?? null);
  }

  function handleDragOver(e: React.DragEvent) {
    e.preventDefault();
    setIsDragOver(true);
  }

  function handleDragLeave() {
    setIsDragOver(false);
  }

  function handleDrop(e: React.DragEvent) {
    e.preventDefault();
    setIsDragOver(false);
    handleFileChange(e.dataTransfer.files?.[0] ?? null);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedFile) return;

    setIsLoading(true);
    setError(null);
    setResult(null);

    try {
      const data = await importWatchlistCsv(watchlistId, selectedFile);
      setResult(data);
      if (data.added > 0) {
        onSuccess();
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Import failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  }

  function handleClose() {
    if (!isLoading) onClose();
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
      onClick={handleClose}
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
            onClick={handleClose}
            disabled={isLoading}
            className="rounded-lg p-1 text-slate-400 transition-colors hover:bg-slate-800 hover:text-white disabled:cursor-not-allowed disabled:opacity-50"
            aria-label="Cancel and close dialog"
          >
            <X className="h-5 w-5" aria-hidden="true" />
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          {/* Drop zone */}
          <div
            role="button"
            tabIndex={0}
            aria-label="Click or drag and drop to select a CSV file"
            className={`mb-4 flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed px-4 py-8 text-center transition-colors ${
              isDragOver
                ? 'border-blue-500 bg-blue-500/10'
                : selectedFile
                ? 'border-slate-600 bg-slate-800/30'
                : 'border-slate-700 bg-slate-800/20 hover:border-slate-600 hover:bg-slate-800/30'
            }`}
            onClick={() => fileInputRef.current?.click()}
            onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') fileInputRef.current?.click(); }}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".csv"
              className="sr-only"
              onChange={handleInputChange}
              aria-hidden="true"
              tabIndex={-1}
            />
            {selectedFile ? (
              <>
                <FileText className="mb-2 h-8 w-8 text-blue-400" aria-hidden="true" />
                <p className="text-sm font-medium text-white">{selectedFile.name}</p>
                <p className="mt-0.5 text-xs text-slate-400">
                  {(selectedFile.size / 1024).toFixed(1)} KB — click to change
                </p>
              </>
            ) : (
              <>
                <Upload className="mb-2 h-8 w-8 text-slate-500" aria-hidden="true" />
                <p className="text-sm text-slate-300">
                  Drop a CSV file here or <span className="text-blue-400">browse</span>
                </p>
                <p className="mt-1 text-xs text-slate-500">
                  Must include a <code className="rounded bg-slate-700 px-1 py-0.5 text-xs">symbol</code> column · max 500 rows · 1 MB
                </p>
              </>
            )}
          </div>

          {/* Error banner */}
          {error && (
            <div
              role="alert"
              className="mb-4 flex items-start gap-2 rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-400"
            >
              <AlertCircle className="mt-0.5 h-4 w-4 flex-shrink-0" aria-hidden="true" />
              <span>{error}</span>
            </div>
          )}

          {/* Import result summary */}
          {result && (
            <div className="mb-4 rounded-lg border border-slate-700 bg-slate-800/50 p-4">
              <div className="mb-2 flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-emerald-400" aria-hidden="true" />
                <span className="text-sm font-medium text-white">Import complete</span>
              </div>
              <p className="text-sm text-slate-300">
                <span className="font-semibold text-emerald-400">{result.added}</span> added
                {result.skipped_duplicates > 0 && (
                  <>, <span className="font-semibold text-amber-400">{result.skipped_duplicates}</span> duplicate{result.skipped_duplicates !== 1 ? 's' : ''} skipped</>
                )}
                {result.skipped_invalid > 0 && (
                  <>, <span className="font-semibold text-red-400">{result.skipped_invalid}</span> invalid</>
                )}
              </p>
              {result.invalid_symbols.length > 0 && (
                <div className="mt-2">
                  <p className="mb-1.5 text-xs text-slate-400">Unrecognised symbols:</p>
                  <div className="flex flex-wrap gap-1.5">
                    {result.invalid_symbols.map((sym) => (
                      <span
                        key={sym}
                        className="rounded bg-red-500/20 px-1.5 py-0.5 text-xs font-mono text-red-400"
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
              type="button"
              onClick={handleClose}
              disabled={isLoading}
              className="rounded-lg border border-slate-700 px-4 py-2 text-sm text-slate-300 transition-colors hover:bg-slate-800 hover:text-white disabled:cursor-not-allowed disabled:opacity-50"
            >
              {result ? 'Close' : 'Cancel'}
            </button>
            {!result && (
              <button
                type="submit"
                disabled={!selectedFile || isLoading}
                className="flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {isLoading ? (
                  <>
                    <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white" aria-hidden="true" />
                    Importing…
                  </>
                ) : (
                  'Import'
                )}
              </button>
            )}
          </div>
        </form>
      </div>
    </div>
  );
}
