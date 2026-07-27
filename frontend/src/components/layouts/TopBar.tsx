import { Bell, Search, Sun, Moon, Monitor } from 'lucide-react';
import { useTheme } from 'next-themes';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { SidebarTrigger } from '@/components/ui/sidebar';
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';

function ThemeToggle() {
  const { theme, setTheme } = useTheme();
  const nextTheme = theme === 'light' ? 'dark' : theme === 'dark' ? 'system' : 'light';

  return (
    <Tooltip>
      <TooltipTrigger render={
        <Button
          variant="ghost"
          size="icon"
          onClick={() => setTheme(nextTheme)}
          title={`Theme: ${theme}`}
        />
      }>
        {theme === 'light' && <Sun className="h-4 w-4" />}
        {theme === 'dark' && <Moon className="h-4 w-4" />}
        {theme === 'system' && <Monitor className="h-4 w-4" />}
        <span className="sr-only">Toggle theme (Ctrl+J)</span>
      </TooltipTrigger>
      <TooltipContent>Theme: {theme} (Ctrl+J)</TooltipContent>
    </Tooltip>
  );
}

interface TopBarProps {
  onCommandOpen?: () => void;
}

export function TopBar({ onCommandOpen }: TopBarProps) {
  const { logout } = useAuth();

  return (
    <header className="flex h-12 items-center justify-between border-b bg-background/80 backdrop-blur-sm px-4 lg:px-6">
      <div className="flex items-center gap-3">
        <SidebarTrigger className="lg:hidden" />
        <div className="hidden md:block">
          <h1 className="text-sm font-semibold text-muted-foreground tracking-wide uppercase">UPCP</h1>
        </div>
      </div>
      <div className="flex items-center gap-1">
        <Button
          variant="outline"
          className="hidden sm:flex h-8 w-56 justify-start gap-2 text-muted-foreground"
          onClick={onCommandOpen}
        >
          <Search className="h-3.5 w-3.5" />
          <span className="flex-1 text-left text-xs">Search or jump to...</span>
          <kbd className="pointer-events-none inline-flex h-5 select-none items-center gap-0.5 rounded border bg-muted px-1.5 font-mono text-[10px] font-medium text-muted-foreground">
            Ctrl K
          </kbd>
        </Button>
        <Tooltip>
          <TooltipTrigger render={<Button variant="ghost" size="icon" className="h-8 w-8" onClick={onCommandOpen} />}>
            <Search className="h-4 w-4 sm:hidden" />
          </TooltipTrigger>
          <TooltipContent>Search (Ctrl+K)</TooltipContent>
        </Tooltip>
        <ThemeToggle />
        <Tooltip>
          <TooltipTrigger render={<Button variant="ghost" size="icon" className="relative h-8 w-8" aria-label="Notifications" />}>
            <Bell className="h-4 w-4" />
            <span className="absolute -right-0.5 -top-0.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-primary px-1 text-[10px] font-medium text-primary-foreground animate-badge-pop">
              3
            </span>
          </TooltipTrigger>
          <TooltipContent>Notifications</TooltipContent>
        </Tooltip>
        <DropdownMenu>
          <DropdownMenuTrigger className="rounded-full ml-1">
            <Avatar className="h-7 w-7">
              <AvatarImage src="/avatars/user.jpg" alt="User" />
              <AvatarFallback className="text-xs">U</AvatarFallback>
            </Avatar>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-48">
            <DropdownMenuGroup>
              <DropdownMenuLabel className="text-xs">My Account</DropdownMenuLabel>
            </DropdownMenuGroup>
            <DropdownMenuSeparator />
            <DropdownMenuGroup>
              <DropdownMenuItem onClick={() => {}}>Profile</DropdownMenuItem>
              <DropdownMenuItem onClick={() => {}}>Settings</DropdownMenuItem>
            </DropdownMenuGroup>
            <DropdownMenuSeparator />
            <DropdownMenuGroup>
              <DropdownMenuItem className="text-destructive" onClick={() => logout()}>Logout</DropdownMenuItem>
            </DropdownMenuGroup>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  );
}
