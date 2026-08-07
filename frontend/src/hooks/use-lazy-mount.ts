import { useCallback, useRef, useState } from 'react';

/**
 * Lazy-mount pattern for dialogs/sheets.
 * Returns `{ mounted, onOpenChange }` — content renders only after first open.
 * Once opened, content stays mounted (no re-mount on re-open).
 */
export function useLazyMount(open: boolean, onOpenChange: (open: boolean) => void) {
  const [mounted, setMounted] = useState(false);
  const hasOpened = useRef(false);

  const handleOpenChange = useCallback(
    (nextOpen: boolean) => {
      if (nextOpen && !hasOpened.current) {
        hasOpened.current = true;
        setMounted(true);
      }
      onOpenChange(nextOpen);
    },
    [onOpenChange],
  );

  return { mounted: mounted || open, onOpenChange: handleOpenChange };
}
