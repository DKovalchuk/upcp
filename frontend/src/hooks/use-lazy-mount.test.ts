import { renderHook, act } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { useLazyMount } from './use-lazy-mount';

describe('useLazyMount', () => {
  it('returns mounted=false when not yet opened', () => {
    const onOpenChange = vi.fn();
    const { result } = renderHook(() => useLazyMount(false, onOpenChange));
    expect(result.current.mounted).toBe(false);
  });

  it('returns mounted=true when open=true', () => {
    const onOpenChange = vi.fn();
    const { result } = renderHook(() => useLazyMount(true, onOpenChange));
    expect(result.current.mounted).toBe(true);
  });

  it('mounts on first open', () => {
    const onOpenChange = vi.fn();
    const { result } = renderHook(
      ({ open }) => useLazyMount(open, onOpenChange),
      { initialProps: { open: false } },
    );

    expect(result.current.mounted).toBe(false);

    act(() => {
      result.current.onOpenChange(true);
    });

    expect(onOpenChange).toHaveBeenCalledWith(true);
    expect(result.current.mounted).toBe(true);
  });

  it('stays mounted after first open even when closed', () => {
    const onOpenChange = vi.fn();
    const { result } = renderHook(
      ({ open }) => useLazyMount(open, onOpenChange),
      { initialProps: { open: false } },
    );

    // Open
    act(() => {
      result.current.onOpenChange(true);
    });
    expect(result.current.mounted).toBe(true);

    // Close via the hook's onOpenChange
    act(() => {
      result.current.onOpenChange(false);
    });

    // onOpenChange was called with false
    expect(onOpenChange).toHaveBeenCalledWith(false);
    // Content stays mounted (useRef tracks first open)
    expect(result.current.mounted).toBe(true);
  });

  it('delegates onOpenChange to parent callback', () => {
    const onOpenChange = vi.fn();
    const { result } = renderHook(() => useLazyMount(false, onOpenChange));

    act(() => {
      result.current.onOpenChange(true);
    });

    expect(onOpenChange).toHaveBeenCalledTimes(1);
    expect(onOpenChange).toHaveBeenCalledWith(true);
  });

  it('does not re-mount on subsequent opens', () => {
    const onOpenChange = vi.fn();
    const { result } = renderHook(
      ({ open }) => useLazyMount(open, onOpenChange),
      { initialProps: { open: false } },
    );

    // Open
    act(() => {
      result.current.onOpenChange(true);
    });
    expect(result.current.mounted).toBe(true);

    // Close
    act(() => {
      result.current.onOpenChange(false);
    });

    // Open again
    act(() => {
      result.current.onOpenChange(true);
    });

    // onOpenChange called 3 times (open, close, open)
    expect(onOpenChange).toHaveBeenCalledTimes(3);
    expect(result.current.mounted).toBe(true);
  });
});
