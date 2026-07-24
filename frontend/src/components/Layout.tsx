import { Outlet } from '@tanstack/react-router';
import { Button } from '@/components/ui/button';

export function Layout() {
  return (
    <div className="min-h-screen bg-background">
      <header className="border-b">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <h1 className="text-2xl font-bold">UPCP</h1>
          <nav className="flex items-center gap-4">
            <Button variant="ghost" size="sm">
              Projects
            </Button>
            <Button variant="ghost" size="sm">
              Settings
            </Button>
          </nav>
        </div>
      </header>
      <main className="container mx-auto px-4 py-8">
        <Outlet />
      </main>
    </div>
  );
}