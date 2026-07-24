import { render } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { PageSkeleton } from './PageSkeleton';

describe('PageSkeleton', () => {
  it('renders header skeleton by default', () => {
    const { container } = render(<PageSkeleton />);
    const skeletons = container.querySelectorAll('[data-slot="skeleton"]');
    expect(skeletons.length).toBeGreaterThan(0);
  });

  it('renders card skeletons when hasCards is true', () => {
    const { container } = render(<PageSkeleton hasCards cardCount={4} />);
    const skeletons = container.querySelectorAll('[data-slot="skeleton"]');
    expect(skeletons.length).toBeGreaterThanOrEqual(4);
  });

  it('renders table row skeletons when hasTable is true', () => {
    const { container } = render(<PageSkeleton hasTable rows={3} />);
    const skeletons = container.querySelectorAll('[data-slot="skeleton"]');
    expect(skeletons.length).toBeGreaterThanOrEqual(3);
  });

  it('renders correct number of table rows', () => {
    const { container } = render(<PageSkeleton hasTable rows={10} />);
    const skeletons = container.querySelectorAll('[data-slot="skeleton"]');
    expect(skeletons.length).toBeGreaterThanOrEqual(10);
  });

  it('hides header when hasHeader is false', () => {
    const { container } = render(<PageSkeleton hasHeader={false} hasTable={false} hasCards={false} />);
    const skeletons = container.querySelectorAll('[data-slot="skeleton"]');
    expect(skeletons.length).toBe(0);
  });
});
