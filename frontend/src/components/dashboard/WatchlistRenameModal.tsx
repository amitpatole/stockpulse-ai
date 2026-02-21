'use client';

import { useEffect, useRef, useState } from 'react';
import { X, Pencil } from 'lucide-react';

interface Props {
  ticker: string;
  currentName: string;
  onConfirm: (newName: string) => void;
  onClose: () => void;
  triggerRef: React.RefObject<HTMLButtonElement | null>;
}

export default function WatchlistRenameModal({ ticker, currentName, onConfirm, onClose, triggerRef }: Props) {
  const [name, setName] = useState(currentName);
  const dialogRef = useRef<HTMLDivElement>(null);
  const headingId = `rename-dlg-${ticker}`;

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;

    const selectors = 'button:not([disabled]), [href], input:not([disabled]), [tabindex]:not([tabindex="-1"])';
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

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const trimmed = name.trim();
    if (trimmed) onConfirm(trimmed);
  }

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
        className="relative w-full max-w-sm rounded-xl border border-slate-700 bg-slate-900 p-6 shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="mb-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Pencil className="h-5 w-5 text-blue-400" aria-hidden="true" />
            <h2 id={headingId} className="text-lg font-semibold text-white">
              Rename {ticker}
            </h2>
          </div>
          <button
            onClick={onClose}
            className="rounded-lg p-1 text-slate-400 transition-colors hover:bg-slate-800 hover:text-white"
            aria-label="Cancel and close dialog"
          >
            <X className="h-5 w-5" aria-hidden="true" />
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          <label
            htmlFor={`rename-input-${ticker}`}
            className="mb-1.5 block text-sm text-slate-400"
          >
            Display name
          </label>
          <input
            id={`rename-input-${ticker}`}
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            maxLength={80}
            className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-sm text-white placeholder-slate-500 outline-none transition-colors focus:border-blue-500 focus:ring-1 focus:ring-blue-500/50"
            placeholder="Enter display name"
          />
          <div className="mt-4 flex justify-end gap-3">
            <button
              type="button"
              onClick={onClose}
              className="rounded-lg border border-slate-700 px-4 py-2 text-sm text-slate-300 transition-colors hover:bg-slate-800 hover:text-white"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={!name.trim()}
              className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-50"
            >
              Save
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
