import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi, afterEach, afterAll } from 'vitest';
import { ErrorBoundary } from './ErrorBoundary';

function ThrowingComponent() {
  throw new Error('Test error');
  return null;
}

describe('ErrorBoundary', () => {
  const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

  afterEach(() => {
    consoleSpy.mockClear();
  });

  afterAll(() => {
    consoleSpy.mockRestore();
  });

  it('renders children when no error', () => {
    render(
      <ErrorBoundary>
        <div>Child content</div>
      </ErrorBoundary>
    );
    expect(screen.getByText('Child content')).toBeInTheDocument();
  });

  it('renders fallback UI when error occurs', () => {
    render(
      <ErrorBoundary>
        <ThrowingComponent />
      </ErrorBoundary>
    );
    expect(screen.getByText('Something went wrong')).toBeInTheDocument();
    expect(screen.getByText(/An unexpected error occurred/)).toBeInTheDocument();
  });

  it('renders reload button', () => {
    render(
      <ErrorBoundary>
        <ThrowingComponent />
      </ErrorBoundary>
    );
    expect(screen.getByRole('button', { name: /Reload page/i })).toBeInTheDocument();
  });

  it('logs error to console', () => {
    render(
      <ErrorBoundary>
        <ThrowingComponent />
      </ErrorBoundary>
    );
    expect(consoleSpy).toHaveBeenCalled();
  });
});
