import { useEffect, useCallback } from 'react';

interface UseKeyboardNavOptions {
  onSelect?: () => void;
  onEscape?: () => void;
  onPrev?: () => void;
  onNext?: () => void;
  enabled?: boolean;
}

export function useKeyboardNav({
  onSelect,
  onEscape,
  onPrev,
  onNext,
  enabled = true,
}: UseKeyboardNavOptions = {}) {
  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (!enabled) return;
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return;

      switch (e.key) {
        case 'j':
        case 'ArrowDown':
          e.preventDefault();
          onNext?.();
          break;
        case 'k':
        case 'ArrowUp':
          e.preventDefault();
          onPrev?.();
          break;
        case 'Enter':
          if (!e.shiftKey) {
            e.preventDefault();
            onSelect?.();
          }
          break;
        case 'Escape':
          e.preventDefault();
          onEscape?.();
          break;
        case '[':
          e.preventDefault();
          onPrev?.();
          break;
        case ']':
          e.preventDefault();
          onNext?.();
          break;
      }
    },
    [enabled, onSelect, onEscape, onPrev, onNext]
  );

  useEffect(() => {
    if (!enabled) return;
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [enabled, handleKeyDown]);
}
