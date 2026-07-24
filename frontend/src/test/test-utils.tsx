import { render, type RenderOptions } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { ReactNode } from 'react';

function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: 0 },
      mutations: { retry: false },
    },
  });
}

export function renderWithProviders(
  ui: ReactNode,
  options: Omit<RenderOptions, 'wrapper'> & {
    queryClient?: QueryClient;
  } = {}
) {
  const { queryClient, ...renderOptions } = options;
  const qc = queryClient ?? createTestQueryClient();

  return {
    ...render(ui, {
      wrapper: ({ children }) => (
        <QueryClientProvider client={qc}>
          {children}
        </QueryClientProvider>
      ),
      ...renderOptions,
    }),
    queryClient: qc,
  };
}

export { createTestQueryClient };
