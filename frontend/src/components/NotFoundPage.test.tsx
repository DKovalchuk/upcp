import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { NotFoundPage } from './NotFoundPage';

// Mock @tanstack/react-router Link component
vi.mock('@tanstack/react-router', () => ({
  Link: ({ to, children, className, ...props }: { to: string; children: React.ReactNode; className?: string; [key: string]: unknown }) => (
    <a href={to} className={className} {...props}>
      {children}
    </a>
  ),
}));

describe('NotFoundPage', () => {
  it('renders 404 title', () => {
    render(<NotFoundPage />);
    expect(screen.getByText('404')).toBeInTheDocument();
  });

  it('renders "Page not found" message', () => {
    render(<NotFoundPage />);
    expect(screen.getByText('Page not found')).toBeInTheDocument();
  });

  it('renders description text', () => {
    render(<NotFoundPage />);
    expect(screen.getByText(/The page you're looking for/)).toBeInTheDocument();
  });

  it('renders "Back to Dashboard" link', () => {
    render(<NotFoundPage />);
    expect(screen.getByRole('link', { name: /Back to Dashboard/i })).toBeInTheDocument();
  });

  it('links to root path', () => {
    render(<NotFoundPage />);
    const link = screen.getByRole('link', { name: /Back to Dashboard/i });
    expect(link).toHaveAttribute('href', '/');
  });
});
