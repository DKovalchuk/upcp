import { renderHook, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useSSE } from './use-sse';

vi.mock('@/contexts/AuthContext', () => ({
  useAuth: vi.fn(),
}));

vi.mock('@/lib/toast', () => ({
  showToast: {
    info: vi.fn(),
    updated: vi.fn(),
    mutationError: vi.fn(),
  },
}));

import { useAuth } from '@/contexts/AuthContext';

const mockUseAuth = vi.mocked(useAuth);
const fetchSpy = vi.fn();

function createWrapper() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
  };
}

describe('useSSE auth gating (TASK-0139)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Never-resolving fetch: no response to parse, no reconnect loop.
    fetchSpy.mockReturnValue(new Promise(() => {}));
    vi.stubGlobal('fetch', fetchSpy);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('does not connect to the stream when unauthenticated', async () => {
    mockUseAuth.mockReturnValue({ isAuthenticated: false } as never);
    renderHook(() => useSSE(), { wrapper: createWrapper() });
    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 50));
    });
    expect(fetchSpy).not.toHaveBeenCalled();
  });

  it('connects to the stream when authenticated (control)', async () => {
    mockUseAuth.mockReturnValue({ isAuthenticated: true } as never);
    renderHook(() => useSSE(), { wrapper: createWrapper() });
    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 50));
    });
    expect(fetchSpy).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/notifications/stream'),
      expect.anything(),
    );
  });
});
