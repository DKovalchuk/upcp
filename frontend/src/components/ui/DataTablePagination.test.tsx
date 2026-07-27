import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { DataTablePagination } from './DataTablePagination';

describe('DataTablePagination', () => {
  it('renders showing text', () => {
    render(
      <DataTablePagination
        offset={0}
        limit={20}
        total={100}
        onPageChange={() => {}}
        onPageSizeChange={() => {}}
      />
    );
    expect(screen.getByText(/Showing/)).toBeInTheDocument();
    expect(screen.getByText('1–20')).toBeInTheDocument();
  });

  it('shows correct range for page 2', () => {
    render(
      <DataTablePagination
        offset={20}
        limit={20}
        total={100}
        onPageChange={() => {}}
        onPageSizeChange={() => {}}
      />
    );
    expect(screen.getByText('21–40')).toBeInTheDocument();
  });

  it('shows 0 results when total is 0', () => {
    render(
      <DataTablePagination
        offset={0}
        limit={20}
        total={0}
        onPageChange={() => {}}
        onPageSizeChange={() => {}}
      />
    );
    expect(screen.getByText('0–0')).toBeInTheDocument();
  });

  it('disables previous button on first page', () => {
    render(
      <DataTablePagination
        offset={0}
        limit={20}
        total={100}
        onPageChange={() => {}}
        onPageSizeChange={() => {}}
      />
    );
    const prevButton = screen.getAllByRole('button')[0];
    expect(prevButton).toBeDisabled();
  });

  it('disables next button on last page', () => {
    render(
      <DataTablePagination
        offset={80}
        limit={20}
        total={100}
        onPageChange={() => {}}
        onPageSizeChange={() => {}}
      />
    );
    const buttons = screen.getAllByRole('button');
    const nextButton = buttons[buttons.length - 2]; // second to last (last is "last page")
    expect(nextButton).toBeDisabled();
  });

  it('calls onPageChange when next is clicked', () => {
    const onPageChange = vi.fn();
    render(
      <DataTablePagination
        offset={0}
        limit={20}
        total={100}
        onPageChange={onPageChange}
        onPageSizeChange={() => {}}
      />
    );
    // Buttons: first, prev, 1, 2, 3, 4, 5, next, last
    // next is index 7
    const buttons = screen.getAllByRole('button');
    const nextButton = buttons[7];
    fireEvent.click(nextButton);
    expect(onPageChange).toHaveBeenCalledWith(20);
  });

  it('calls onPageChange when page number is clicked', () => {
    const onPageChange = vi.fn();
    render(
      <DataTablePagination
        offset={0}
        limit={20}
        total={100}
        onPageChange={onPageChange}
        onPageSizeChange={() => {}}
      />
    );
    const page2Button = screen.getByRole('button', { name: '2' });
    fireEvent.click(page2Button);
    expect(onPageChange).toHaveBeenCalledWith(20);
  });

  it('renders page size selector', () => {
    render(
      <DataTablePagination
        offset={0}
        limit={20}
        total={100}
        onPageChange={() => {}}
        onPageSizeChange={() => {}}
      />
    );
    const select = screen.getByRole('combobox');
    expect(select).toBeInTheDocument();
  });
});
