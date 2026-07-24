import { useState } from 'react';
import { Outlet } from '@tanstack/react-router';
import { SidebarProvider, SidebarInset } from '@/components/ui/sidebar';
import { AppSidebar } from './AppSidebar';
import { TopBar } from './TopBar';
import { BreadcrumbBar } from './BreadcrumbBar';
import { Separator } from '@/components/ui/separator';
import { TooltipProvider } from '@/components/ui/tooltip';
import { ErrorBoundary } from '@/components/ErrorBoundary';
import { Toaster } from '@/components/ui/sonner';
import { CommandPalette } from '@/components/CommandPalette';

export function AppShell() {
  const [commandOpen, setCommandOpen] = useState(false);

  return (
    <TooltipProvider>
      <SidebarProvider>
        <a
          href="#main-content"
          className="sr-only focus:not-sr-only focus:absolute focus:z-50 focus:px-4 focus:py-2 focus:bg-primary focus:text-primary-foreground"
        >
          Skip to main content
        </a>
        <AppSidebar />
        <SidebarInset>
          <TopBar onCommandOpen={() => setCommandOpen(true)} />
          <Separator />
          <BreadcrumbBar />
          <ErrorBoundary>
            <main id="main-content" className="flex-1 p-4 lg:p-6">
              <Outlet />
            </main>
          </ErrorBoundary>
        </SidebarInset>
        <Toaster position="bottom-right" richColors />
        <CommandPalette open={commandOpen} onOpenChange={setCommandOpen} />
      </SidebarProvider>
    </TooltipProvider>
  );
}
