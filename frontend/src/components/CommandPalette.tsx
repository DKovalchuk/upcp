import { useEffect, useMemo, useState, useCallback } from 'react';
import { useNavigate, useLocation } from '@tanstack/react-router';
import { useQuery } from '@tanstack/react-query';
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
  FileText,
  Search,
} from 'lucide-react';
import { searchGlobal } from '@/lib/api';

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

const ENTITY_ICONS: Record<string, React.ComponentType<{ className?: string }>> = {
  project: FolderKanban,
  feature: GitBranch,
  task: FileText,
};

export function CommandPalette({ open, onOpenChange }: CommandPaletteProps) {
  const navigate = useNavigate();
  const location = useLocation();
  const [searchQuery, setSearchQuery] = useState('');

  const { data: searchResults = [] } = useQuery({
    queryKey: ['search', searchQuery],
    queryFn: () => searchGlobal(searchQuery),
    enabled: searchQuery.length >= 2,
  });

  const handleSearchChange = useCallback((value: string) => {
    setSearchQuery(value);
  }, []);

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
    <CommandDialog open={open} onOpenChange={(v) => { if (!v) setSearchQuery(''); onOpenChange(v); }}>
      <CommandInput placeholder="Type a command or search..." onValueChange={handleSearchChange} />
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

        {searchResults.length > 0 && (
          <>
            <CommandSeparator />
            <CommandGroup heading="Search Results">
              {searchResults.map((result) => {
                const Icon = ENTITY_ICONS[result.entity_type] || Search;
                return (
                  <CommandItem
                    key={`${result.entity_type}-${result.id}`}
                    value={`search:${result.entity_type}:${result.title}`}
                    onSelect={() => go(result.url)}
                  >
                    <Icon className="mr-2 h-4 w-4" />
                    <div className="min-w-0 flex-1">
                      <p className="text-sm">{result.title}</p>
                      {result.subtitle && (
                        <p className="text-xs text-muted-foreground truncate">{result.subtitle}</p>
                      )}
                    </div>
                    <span className="ml-2 text-xs text-muted-foreground capitalize">{result.entity_type}</span>
                  </CommandItem>
                );
              })}
            </CommandGroup>
          </>
        )}
      </CommandList>
    </CommandDialog>
  );
}
