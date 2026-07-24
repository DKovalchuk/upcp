import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { StatusBadge } from './StatusBadge';

describe('StatusBadge', () => {
  it('renders status text', () => {
    render(<StatusBadge status="active" />);
    expect(screen.getByText('active')).toBeInTheDocument();
  });

  it('applies correct colors for active status', () => {
    render(<StatusBadge status="active" />);
    const badge = screen.getByText('active');
    expect(badge.className).toContain('bg-emerald-500/10');
    expect(badge.className).toContain('text-emerald-600');
  });

  it('applies correct colors for backlog status', () => {
    render(<StatusBadge status="backlog" />);
    const badge = screen.getByText('backlog');
    expect(badge.className).toContain('bg-slate-500/10');
  });

  it('applies correct colors for in-progress status', () => {
    render(<StatusBadge status="in-progress" />);
    const badge = screen.getByText('in-progress');
    expect(badge.className).toContain('bg-blue-500/10');
  });

  it('applies correct colors for done status', () => {
    render(<StatusBadge status="done" />);
    const badge = screen.getByText('done');
    expect(badge.className).toContain('bg-violet-500/10');
  });

  it('falls back to backlog colors for unknown status', () => {
    render(<StatusBadge status="unknown-status" />);
    const badge = screen.getByText('unknown-status');
    expect(badge.className).toContain('bg-slate-500/10');
  });
});
