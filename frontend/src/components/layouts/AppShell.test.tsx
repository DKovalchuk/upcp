import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { AppShell } from './AppShell';

vi.mock('@tanstack/react-router', () => ({
  Outlet: () => <div data-testid="outlet">Outlet Content</div>,
  useNavigate: () => vi.fn(),
}));

vi.mock('next-themes', () => ({
  useTheme: () => ({ theme: 'light', setTheme: vi.fn() }),
}));

vi.mock('@/contexts/AuthContext', () => ({
  AuthProvider: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  useAuth: () => ({ logout: vi.fn() }),
}));

vi.mock('@/hooks/use-hotkeys', () => ({
  useHotkeys: vi.fn(),
}));

vi.mock('@/components/layouts/AppSidebar', () => ({
  AppSidebar: () => <div data-testid="sidebar">Sidebar</div>,
}));

vi.mock('@/components/layouts/TopBar', () => ({
  TopBar: ({ onCommandOpen }: { onCommandOpen?: () => void }) => (
    <div data-testid="topbar">
      <button onClick={onCommandOpen}>Open Command</button>
    </div>
  ),
}));

vi.mock('@/components/layouts/BreadcrumbBar', () => ({
  BreadcrumbBar: () => <div data-testid="breadcrumb">Breadcrumb</div>,
}));

vi.mock('@/components/CommandPalette', () => ({
  CommandPalette: ({ open }: { open: boolean }) => (
    <div data-testid="command-palette">{open ? 'Open' : 'Closed'}</div>
  ),
}));

vi.mock('@/components/ui/ShortcutsDialog', () => ({
  ShortcutsDialog: ({ open }: { open: boolean }) => (
    <div data-testid="shortcuts-dialog">{open ? 'Open' : 'Closed'}</div>
  ),
}));

vi.mock('@/components/ErrorBoundary', () => ({
  ErrorBoundary: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

describe('AppShell', () => {
  it('renders sidebar', () => {
    render(<AppShell />);
    expect(screen.getByTestId('sidebar')).toBeInTheDocument();
  });

  it('renders topbar', () => {
    render(<AppShell />);
    expect(screen.getByTestId('topbar')).toBeInTheDocument();
  });

  it('renders breadcrumb', () => {
    render(<AppShell />);
    expect(screen.getByTestId('breadcrumb')).toBeInTheDocument();
  });

  it('renders outlet content', () => {
    render(<AppShell />);
    expect(screen.getByTestId('outlet')).toBeInTheDocument();
  });

  it('renders skip to main content link for accessibility', () => {
    render(<AppShell />);
    expect(screen.getByText('Skip to main content')).toBeInTheDocument();
  });

  it('command palette starts closed', () => {
    render(<AppShell />);
    expect(screen.getByTestId('command-palette')).toHaveTextContent('Closed');
  });
});
