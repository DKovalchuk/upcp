import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { SidebarProvider } from '@/components/ui/sidebar';
import { AppSidebar } from './AppSidebar';

vi.mock('@tanstack/react-router', () => ({
  Link: ({
    to,
    children,
    className,
  }: {
    to: string;
    children: React.ReactNode;
    className?: string;
  }) => (
    <a href={to} className={className}>
      {children}
    </a>
  ),
  useLocation: () => ({ pathname: '/' }),
}));

vi.mock('@/hooks/use-project-id', () => ({ useProjectId: () => null }));

function renderSidebar() {
  return render(
    <SidebarProvider>
      <AppSidebar />
    </SidebarProvider>
  );
}

describe('AppSidebar', () => {
  it('shows the Analytics nav item linking to /analytics', () => {
    renderSidebar();
    const link = screen.getByRole('link', { name: /Analytics/ });
    expect(link).toHaveAttribute('href', '/analytics');
  });

  it('renders nav groups with core items', () => {
    renderSidebar();
    expect(screen.getByText('Main')).toBeInTheDocument();
    expect(screen.getByText('System')).toBeInTheDocument();
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Reports')).toBeInTheDocument();
  });
});
