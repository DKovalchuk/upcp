import { useEffect, useCallback, useRef } from 'react';

interface HotkeyBinding {
  key: string;
  ctrl?: boolean;
  shift?: boolean;
  alt?: boolean;
  sequence?: string;
  action: () => void;
  description?: string;
}

const sequenceTimeout = 1000;

export function useHotkeys(bindings: HotkeyBinding[], enabled = true) {
  const sequenceRef = useRef<string | null>(null);
  const sequenceTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (!enabled) return;
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement || e.target instanceof HTMLSelectElement) return;
      if (e.target instanceof HTMLElement && e.target.isContentEditable) return;

      const isCtrl = e.ctrlKey || e.metaKey;

      for (const binding of bindings) {
        if (binding.sequence) {
          if (sequenceRef.current === binding.sequence && e.key === binding.key) {
            e.preventDefault();
            binding.action();
            sequenceRef.current = null;
            if (sequenceTimerRef.current) clearTimeout(sequenceTimerRef.current);
            return;
          }
          if (e.key === binding.sequence && !isCtrl) {
            sequenceRef.current = binding.sequence;
            sequenceTimerRef.current = setTimeout(() => {
              sequenceRef.current = null;
            }, sequenceTimeout);
            return;
          }
          continue;
        }

        if (binding.ctrl && !isCtrl) continue;
        if (!binding.ctrl && isCtrl) continue;
        if (binding.shift && !e.shiftKey) continue;
        if (binding.alt && !e.altKey) continue;
        if (e.key.toLowerCase() !== binding.key.toLowerCase()) continue;

        e.preventDefault();
        binding.action();
        return;
      }
    },
    [bindings, enabled],
  );

  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      if (sequenceTimerRef.current) clearTimeout(sequenceTimerRef.current);
    };
  }, [handleKeyDown]);
}
