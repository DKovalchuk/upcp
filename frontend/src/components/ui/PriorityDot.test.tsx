import { render } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { PriorityDot } from './PriorityDot';
import { TooltipProvider } from './tooltip';

function renderWithProvider(ui: React.ReactNode) {
  return render(<TooltipProvider>{ui}</TooltipProvider>);
}

describe('PriorityDot', () => {
  it('renders a dot element', () => {
    renderWithProvider(<PriorityDot priority={0} />);
    const dot = document.querySelector('.rounded-full');
    expect(dot).toBeInTheDocument();
  });

  it('applies red color for priority 0 (Critical)', () => {
    renderWithProvider(<PriorityDot priority={0} />);
    const dot = document.querySelector('.rounded-full');
    expect(dot?.className).toContain('bg-red-500');
  });

  it('applies orange color for priority 1 (High)', () => {
    renderWithProvider(<PriorityDot priority={1} />);
    const dot = document.querySelector('.rounded-full');
    expect(dot?.className).toContain('bg-orange-500');
  });

  it('applies yellow color for priority 2 (Medium)', () => {
    renderWithProvider(<PriorityDot priority={2} />);
    const dot = document.querySelector('.rounded-full');
    expect(dot?.className).toContain('bg-yellow-500');
  });

  it('applies green color for priority 3 (Low)', () => {
    renderWithProvider(<PriorityDot priority={3} />);
    const dot = document.querySelector('.rounded-full');
    expect(dot?.className).toContain('bg-green-500');
  });

  it('maps high values (4+) to Low color', () => {
    renderWithProvider(<PriorityDot priority={10} />);
    const dot = document.querySelector('.rounded-full');
    expect(dot?.className).toContain('bg-green-500');
  });

  it('maps negative values to Critical color', () => {
    renderWithProvider(<PriorityDot priority={-1} />);
    const dot = document.querySelector('.rounded-full');
    expect(dot?.className).toContain('bg-red-500');
  });
});
