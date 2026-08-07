import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { CommandPalette } from './CommandPalette';

const mockNavigate = vi.fn();
let mockPathname = '/projects';

vi.mock('@tanstack/react-router', () => ({
  useNavigate: () => mockNavigate,
  useLocation: () => ({ pathname: mockPathname }),
}));

vi.mock('@/lib/api', () => ({
  searchGlobal: vi.fn().mockResolvedValue([]),
}));

function renderPalette(props: Partial<React.ComponentProps<typeof CommandPalette>> = {}) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <CommandPalette open={true} onOpenChange={vi.fn()} {...props} />
    </QueryClientProvider>
  );
}

describe('CommandPalette', () => {
  beforeEach(() => {
    mockNavigate.mockClear();
    mockPathname = '/projects';
  });

  it('does not render when closed', () => {
    const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    const { unmount } = render(
      <QueryClientProvider client={qc}>
        <CommandPalette open={false} onOpenChange={vi.fn()} />
      </QueryClientProvider>
    );
    expect(screen.queryByPlaceholderText('Type a command or search...')).not.toBeInTheDocument();
    unmount();
  });

  it('renders when open', () => {
    renderPalette();
    expect(screen.getByPlaceholderText('Type a command or search...')).toBeInTheDocument();
  });

  it('shows navigation commands', () => {
    renderPalette();
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Projects')).toBeInTheDocument();
    expect(screen.getByText('Health')).toBeInTheDocument();
  });

  it('filters commands by typing', async () => {
    renderPalette();
    const input = screen.getByPlaceholderText('Type a command or search...');
    fireEvent.change(input, { target: { value: 'health' } });
    await waitFor(() => {
      expect(screen.getByText('Health')).toBeInTheDocument();
      expect(screen.queryByText('Dashboard')).not.toBeInTheDocument();
    });
  });

  it('navigates on command select', () => {
    const onOpenChange = vi.fn();
    renderPalette({ onOpenChange });
    fireEvent.click(screen.getByText('Dashboard'));
    expect(mockNavigate).toHaveBeenCalledWith({ to: '/' });
    expect(onOpenChange).toHaveBeenCalledWith(false);
  });

  it('passes onOpenChange to CommandDialog', () => {
    renderPalette();
    expect(screen.getByPlaceholderText('Type a command or search...')).toBeInTheDocument();
  });

  it('shows project-specific commands when on project page', () => {
    mockPathname = '/projects/proj-123/delivery';
    renderPalette();
    expect(screen.getByText('Structure')).toBeInTheDocument();
    expect(screen.getByText('Delivery')).toBeInTheDocument();
    expect(screen.getByText('Quality')).toBeInTheDocument();
    expect(screen.getByText('Audit')).toBeInTheDocument();
  });

  it('shows Actions group with New Project', () => {
    renderPalette();
    expect(screen.getByText('New Project')).toBeInTheDocument();
  });

  it('shows project actions when on project page', () => {
    mockPathname = '/projects/proj-123/delivery';
    renderPalette();
    expect(screen.getByText('New Feature')).toBeInTheDocument();
    expect(screen.getByText('Refresh Data')).toBeInTheDocument();
  });

  it('dispatches upcp:action event for Refresh Data', () => {
    const onOpenChange = vi.fn();
    const dispatchSpy = vi.spyOn(window, 'dispatchEvent');
    mockPathname = '/projects/proj-123/delivery';
    renderPalette({ onOpenChange });

    fireEvent.click(screen.getByText('Refresh Data'));

    expect(dispatchSpy).toHaveBeenCalledWith(
      expect.objectContaining({
        type: 'upcp:action',
        detail: 'refresh',
      }),
    );
    expect(onOpenChange).toHaveBeenCalledWith(false);
    dispatchSpy.mockRestore();
  });

  it('navigates to delivery and dispatches new-feature action', () => {
    mockPathname = '/projects/proj-123/delivery';
    renderPalette();

    fireEvent.click(screen.getByText('New Feature'));

    expect(mockNavigate).toHaveBeenCalledWith({ to: '/projects/proj-123/delivery' });
  });
});
