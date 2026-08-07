import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { TopBar } from './TopBar';

const mockSetTheme = vi.fn();
vi.mock('next-themes', () => ({
  useTheme: () => ({ theme: 'light', setTheme: mockSetTheme }),
}));

const mockLogout = vi.fn();
vi.mock('@/contexts/AuthContext', () => ({
  useAuth: () => ({ logout: mockLogout }),
}));

vi.mock('@/components/notifications/NotificationBell', () => ({
  NotificationBell: () => <div data-testid="notification-bell" />,
}));

vi.mock('@/components/ui/sidebar', () => ({
  SidebarTrigger: ({ className }: { className?: string }) => (
    <button className={className} data-testid="sidebar-trigger">Menu</button>
  ),
}));

describe('TopBar', () => {
  const defaultProps = { onCommandOpen: vi.fn() };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders UPCP branding', () => {
    render(<TopBar {...defaultProps} />);
    expect(screen.getByText('UPCP')).toBeInTheDocument();
  });

  it('renders search button with Ctrl+K hint', () => {
    render(<TopBar {...defaultProps} />);
    expect(screen.getByText('Ctrl K')).toBeInTheDocument();
  });

  it('calls onCommandOpen when search clicked', () => {
    render(<TopBar {...defaultProps} />);
    fireEvent.click(screen.getByText('Search or jump to...'));
    expect(defaultProps.onCommandOpen).toHaveBeenCalled();
  });

  it('calls onCommandOpen when mobile search clicked', () => {
    render(<TopBar {...defaultProps} />);
    fireEvent.click(screen.getByLabelText('Search (Ctrl+K)'));
    expect(defaultProps.onCommandOpen).toHaveBeenCalled();
  });

  it('cycles theme on theme toggle click', () => {
    render(<TopBar {...defaultProps} />);
    fireEvent.click(screen.getByLabelText('Theme: light'));
    expect(mockSetTheme).toHaveBeenCalledWith('dark');
  });

  it('calls logout when Logout clicked', () => {
    render(<TopBar {...defaultProps} />);
    // Open dropdown by clicking avatar
    fireEvent.click(screen.getByText('U'));
    fireEvent.click(screen.getByText('Logout'));
    expect(mockLogout).toHaveBeenCalled();
  });

  it('shows notification bell', () => {
    render(<TopBar {...defaultProps} />);
    expect(screen.getByTestId('notification-bell')).toBeInTheDocument();
  });

  it('shows user avatar', () => {
    render(<TopBar {...defaultProps} />);
    expect(screen.getByText('U')).toBeInTheDocument();
  });

  it('shows sidebar trigger', () => {
    render(<TopBar {...defaultProps} />);
    expect(screen.getByTestId('sidebar-trigger')).toBeInTheDocument();
  });
});
