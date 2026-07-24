import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { EmptyState } from './EmptyState';
import { FolderKanban } from 'lucide-react';

describe('EmptyState', () => {
  it('renders title', () => {
    render(
      <EmptyState icon={FolderKanban} title="No items found" />
    );
    expect(screen.getByText('No items found')).toBeInTheDocument();
  });

  it('renders description when provided', () => {
    render(
      <EmptyState
        icon={FolderKanban}
        title="Empty"
        description="Create your first item"
      />
    );
    expect(screen.getByText('Create your first item')).toBeInTheDocument();
  });

  it('renders action button when provided', () => {
    const onClick = vi.fn();
    render(
      <EmptyState
        icon={FolderKanban}
        title="Empty"
        action={{ label: 'Create Item', onClick }}
      />
    );
    const button = screen.getByRole('button', { name: 'Create Item' });
    expect(button).toBeInTheDocument();
    fireEvent.click(button);
    expect(onClick).toHaveBeenCalledTimes(1);
  });

  it('does not render action button when not provided', () => {
    render(<EmptyState icon={FolderKanban} title="Empty" />);
    expect(screen.queryByRole('button')).not.toBeInTheDocument();
  });

  it('renders the icon', () => {
    render(<EmptyState icon={FolderKanban} title="Empty" />);
    const icon = document.querySelector('svg');
    expect(icon).toBeInTheDocument();
  });
});
