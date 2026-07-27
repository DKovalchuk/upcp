import { useState, useCallback } from 'react';
import { Outlet, useNavigate } from '@tanstack/react-router';
import { SidebarProvider, SidebarInset } from '@/components/ui/sidebar';
import { AppSidebar } from './AppSidebar';
import { TopBar } from './TopBar';
import { BreadcrumbBar } from './BreadcrumbBar';
import { Separator } from '@/components/ui/separator';
import { TooltipProvider } from '@/components/ui/tooltip';
import { ErrorBoundary } from '@/components/ErrorBoundary';
import { Toaster } from '@/components/ui/sonner';
import { CommandPalette } from '@/components/CommandPalette';
import { ShortcutsDialog } from '@/components/ui/ShortcutsDialog';
import { useHotkeys } from '@/hooks/use-hotkeys';
import { useTheme } from 'next-themes';

export function AppShell() {
  const [commandOpen, setCommandOpen] = useState(false);
  const [shortcutsOpen, setShortcutsOpen] = useState(false);
  const navigate = useNavigate();
  const { theme, setTheme } = useTheme();

  const toggleTheme = useCallback(() => {
    if (theme === 'light') setTheme('dark');
    else if (theme === 'dark') setTheme('system');
    else setTheme('light');
  }, [theme, setTheme]);

  useHotkeys([
    { key: 'k', ctrl: true, action: () => setCommandOpen(true), description: 'Command palette' },
    { key: '?', action: () => setShortcutsOpen(true), description: 'Show shortcuts' },
    { key: 'j', ctrl: true, action: toggleTheme, description: 'Toggle theme' },
    { key: 'd', sequence: 'g', action: () => navigate({ to: '/' }), description: 'Go to Dashboard' },
    { key: 'p', sequence: 'g', action: () => navigate({ to: '/projects' }), description: 'Go to Projects' },
    { key: 'r', sequence: 'g', action: () => navigate({ to: '/reports' }), description: 'Go to Reports' },
    { key: 's', sequence: 'g', action: () => navigate({ to: '/settings' }), description: 'Go to Settings' },
  ]);

  return (
    <TooltipProvider>
      <SidebarProvider>
        <a
          href="#main-content"
          className="sr-only focus:not-sr-only focus:absolute focus:z-50 focus:px-4 focus:py-2 focus:bg-primary focus:text-primary-foreground focus:rounded-md"
        >
          Skip to main content
        </a>
        <AppSidebar />
        <SidebarInset>
          <TopBar onCommandOpen={() => setCommandOpen(true)} />
          <Separator />
          <BreadcrumbBar />
          <ErrorBoundary>
            <main id="main-content" className="flex-1 overflow-x-hidden p-4 lg:p-6">
              <Outlet />
            </main>
          </ErrorBoundary>
        </SidebarInset>
        <Toaster position="bottom-right" richColors />
        <CommandPalette open={commandOpen} onOpenChange={setCommandOpen} />
        <ShortcutsDialog open={shortcutsOpen} onOpenChange={setShortcutsOpen} />
      </SidebarProvider>
    </TooltipProvider>
  );
}
