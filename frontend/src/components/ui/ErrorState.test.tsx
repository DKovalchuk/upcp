import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { ErrorState } from './ErrorState';

describe('ErrorState', () => {
  it('renders default title', () => {
    render(<ErrorState message="Something broke" />);
    expect(screen.getByText('Error')).toBeInTheDocument();
  });

  it('renders custom title', () => {
    render(<ErrorState title="Custom Error" message="Details here" />);
    expect(screen.getByText('Custom Error')).toBeInTheDocument();
  });

  it('renders error message', () => {
    render(<ErrorState message="Connection timeout" />);
    expect(screen.getByText('Connection timeout')).toBeInTheDocument();
  });

  it('renders retry button when onRetry provided', () => {
    const onRetry = vi.fn();
    render(<ErrorState message="Failed" onRetry={onRetry} />);
    const button = screen.getByRole('button', { name: /Try Again/i });
    expect(button).toBeInTheDocument();
    fireEvent.click(button);
    expect(onRetry).toHaveBeenCalledTimes(1);
  });

  it('does not render retry button when onRetry not provided', () => {
    render(<ErrorState message="Failed" />);
    expect(screen.queryByRole('button')).not.toBeInTheDocument();
  });
});
