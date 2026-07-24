import { useEffect, useMemo } from 'react';
import { useNavigate, useLocation } from '@tanstack/react-router';
import {
  CommandDialog,
  CommandInput,
  CommandList,
  CommandEmpty,
  CommandGroup,
  CommandItem,
  CommandShortcut,
  CommandSeparator,
} from '@/components/ui/command';
import {
  LayoutDashboard,
  FolderKanban,
  Activity,
  Boxes,
  GitBranch,
  ShieldCheck,
  ScrollText,
  Settings,
} from 'lucide-react';

interface CommandPaletteProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

interface Command {
  id: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  shortcut?: string;
  action: () => void;
}

export function CommandPalette({ open, onOpenChange }: CommandPaletteProps) {
  const navigate = useNavigate();
  const location = useLocation();

  const projectId = useMemo(() => {
    const match = location.pathname.match(/^\/projects\/([^/]+)/);
    return match?.[1] ?? null;
  }, [location.pathname]);

  const go = (path: string) => {
    navigate({ to: path });
    onOpenChange(false);
  };

  const globalCommands: Command[] = [
    {
      id: 'dashboard',
      label: 'Dashboard',
      icon: LayoutDashboard,
      shortcut: 'G D',
      action: () => go('/'),
    },
    {
      id: 'projects',
      label: 'Projects',
      icon: FolderKanban,
      shortcut: 'G P',
      action: () => go('/projects'),
    },
    {
      id: 'health',
      label: 'Health',
      icon: Activity,
      shortcut: 'G H',
      action: () => go('/health'),
    },
  ];

  const projectCommands: Command[] = projectId
    ? [
        {
          id: 'overview',
          label: 'Overview',
          icon: Boxes,
          action: () => go(`/projects/${projectId}`),
        },
        {
          id: 'structure',
          label: 'Structure',
          icon: Boxes,
          action: () => go(`/projects/${projectId}/structure`),
        },
        {
          id: 'delivery',
          label: 'Delivery',
          icon: GitBranch,
          action: () => go(`/projects/${projectId}/delivery`),
        },
        {
          id: 'quality',
          label: 'Quality',
          icon: ShieldCheck,
          action: () => go(`/projects/${projectId}/quality`),
        },
        {
          id: 'audit',
          label: 'Audit',
          icon: ScrollText,
          action: () => go(`/projects/${projectId}/audit`),
        },
        {
          id: 'settings',
          label: 'Project Settings',
          icon: Settings,
          action: () => go(`/projects/${projectId}/settings`),
        },
      ]
    : [];

  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (e.key === 'k' && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        onOpenChange(!open);
      }
    };
    document.addEventListener('keydown', down);
    return () => document.removeEventListener('keydown', down);
  }, [open, onOpenChange]);

  return (
    <CommandDialog open={open} onOpenChange={onOpenChange}>
      <CommandInput placeholder="Type a command or search..." />
      <CommandList>
        <CommandEmpty>No results found.</CommandEmpty>

        <CommandGroup heading="Navigation">
          {globalCommands.map((cmd) => (
            <CommandItem
              key={cmd.id}
              value={cmd.label}
              onSelect={cmd.action}
            >
              <cmd.icon className="mr-2 h-4 w-4" />
              {cmd.label}
              {cmd.shortcut && <CommandShortcut>{cmd.shortcut}</CommandShortcut>}
            </CommandItem>
          ))}
        </CommandGroup>

        {projectCommands.length > 0 && (
          <>
            <CommandSeparator />
            <CommandGroup heading="Project">
              {projectCommands.map((cmd) => (
                <CommandItem
                  key={cmd.id}
                  value={cmd.label}
                  onSelect={cmd.action}
                >
                  <cmd.icon className="mr-2 h-4 w-4" />
                  {cmd.label}
                </CommandItem>
              ))}
            </CommandGroup>
          </>
        )}
      </CommandList>
    </CommandDialog>
  );
}
