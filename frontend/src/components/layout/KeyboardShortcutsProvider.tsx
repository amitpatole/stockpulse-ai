'use client';

import { createContext, useCallback, useContext, useRef, useState } from 'react';
import { useKeyboardShortcuts } from '@/hooks/useKeyboardShortcuts';
import KeyboardShortcutsModal from '@/components/KeyboardShortcutsModal';

interface KeyboardShortcutsContextValue {
  registerSearchInput: (el: HTMLInputElement | null) => void;
}

const KeyboardShortcutsContext = createContext<KeyboardShortcutsContextValue>({
  registerSearchInput: () => {},
});

export function useKeyboardShortcutsContext() {
  return useContext(KeyboardShortcutsContext);
}

export default function KeyboardShortcutsProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const searchRef = useRef<HTMLInputElement | null>(null);
  const [isHelpOpen, setIsHelpOpen] = useState(false);

  const registerSearchInput = useCallback((el: HTMLInputElement | null) => {
    searchRef.current = el;
  }, []);

  const openHelp = useCallback(() => setIsHelpOpen(true), []);
  const closeHelp = useCallback(() => setIsHelpOpen(false), []);

  useKeyboardShortcuts({
    searchRef,
    onOpenHelp: openHelp,
    onCloseHelp: closeHelp,
    isHelpOpen,
  });

  return (
    <KeyboardShortcutsContext.Provider value={{ registerSearchInput }}>
      {children}
      <KeyboardShortcutsModal isOpen={isHelpOpen} onClose={closeHelp} />
    </KeyboardShortcutsContext.Provider>
  );
}
