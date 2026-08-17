import { vi } from 'vitest';
import type { UseQueryResult } from '@tanstack/react-query';

/**
 * Create a partial UseQueryResult for mocking hooks in tests.
 * Omits mutation-related fields that aren't needed in query mocks.
 */
export function mockQueryResult<T>(overrides: Partial<UseQueryResult<T>> = {}): UseQueryResult<T> {
  return {
    data: undefined,
    dataUpdatedAt: 0,
    error: null,
    errorUpdatedAt: 0,
    failureCount: 0,
    failureReason: null,
    fetchStatus: 'idle',
    isError: false,
    isFetched: false,
    isFetchedAfterMount: false,
    isFetching: false,
    isInitialLoading: false,
    isLoading: true,
    isLoadingError: false,
    isPending: true,
    isPlaceholderData: false,
    isRefetchError: false,
    isRefetching: false,
    isStale: true,
    isSuccess: false,
    refetch: vi.fn() as never,
    status: 'pending',
    ...overrides,
  } as UseQueryResult<T>;
}

export function mockSuccessQuery<T>(data: T): UseQueryResult<T> {
  return mockQueryResult({
    data,
    fetchStatus: 'idle',
    isError: false,
    isFetched: true,
    isFetching: false,
    isInitialLoading: false,
    isLoading: false,
    isPending: false,
    isSuccess: true,
    status: 'success',
  });
}

export function mockErrorQuery(message: string): UseQueryResult<never> {
  return mockQueryResult({
    error: new Error(message),
    isError: true,
    isFetched: true,
    isFetching: false,
    isLoading: false,
    isLoadingError: true,
    isPending: false,
    isRefetchError: false,
    isSuccess: false,
    status: 'error',
  });
}

export function mockLoadingQuery<T>(): UseQueryResult<T> {
  return mockQueryResult<T>({
    isLoading: true,
    isPending: true,
    isFetching: true,
    isSuccess: false,
    status: 'pending',
  });
}
