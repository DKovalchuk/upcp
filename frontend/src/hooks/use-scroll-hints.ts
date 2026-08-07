import { useCallback, useRef } from 'react';

export function useScrollHints() {
  const ref = useRef<HTMLDivElement>(null);

  const onScroll = useCallback(() => {
    const el = ref.current;
    if (!el) return;
    const canLeft = el.scrollLeft > 4;
    const canRight = el.scrollLeft + el.clientWidth < el.scrollWidth - 4;
    el.setAttribute('data-can-scroll-left', String(canLeft));
    el.setAttribute('data-can-scroll-right', String(canRight));
  }, []);

  const check = useCallback(() => {
    requestAnimationFrame(onScroll);
  }, [onScroll]);

  return { ref, onScroll, check };
}
