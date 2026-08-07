import { useEffect, useState, useCallback } from 'react';
import { useNavigate } from '@tanstack/react-router';
import { useQuery } from '@tanstack/react-query';
import { useProjectId } from '@/hooks/use-project-id';
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
  BarChart3,
  Clock,
  Plus,
  Zap,
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
  category: string;
  action: () => void;
}

const ENTITY_ICONS: Record<string, React.ComponentType<{ className?: string }>> = {
  project: FolderKanban,
  feature: GitBranch,
  task: FileText,
};

function getRecentItems(): string[] {
  try {
    return JSON.parse(localStorage.getItem('upcp:recent-commands') || '[]');
  } catch {
    return [];
  }
}

function saveRecentItem(id: string) {
  const recent = getRecentItems().filter((r) => r !== id);
  recent.unshift(id);
  localStorage.setItem('upcp:recent-commands', JSON.stringify(recent.slice(0, 5)));
}

export function CommandPalette({ open, onOpenChange }: CommandPaletteProps) {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');

  const { data: searchResults = [] } = useQuery({
    queryKey: ['search', searchQuery],
    queryFn: () => searchGlobal(searchQuery),
    enabled: searchQuery.length >= 2,
  });

  const handleSearchChange = useCallback((value: string) => {
    setSearchQuery(value);
  }, []);

  const projectId = useProjectId();

  const go = (path: string) => {
    navigate({ to: path });
    onOpenChange(false);
  };

  const executeCommand = (cmd: Command) => {
    saveRecentItem(cmd.id);
    cmd.action();
  };

  const globalCommands: Command[] = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard, shortcut: 'G D', category: 'Navigation', action: () => go('/') },
    { id: 'projects', label: 'Projects', icon: FolderKanban, shortcut: 'G P', category: 'Navigation', action: () => go('/projects') },
    { id: 'reports', label: 'Reports', icon: BarChart3, shortcut: 'G R', category: 'Navigation', action: () => go('/reports') },
    { id: 'health', label: 'Health', icon: Activity, shortcut: 'G H', category: 'Navigation', action: () => go('/health') },
    { id: 'settings', label: 'Settings', icon: Settings, shortcut: 'G S', category: 'Navigation', action: () => go('/settings') },
  ];

  const projectCommands: Command[] = projectId
    ? [
        { id: 'overview', label: 'Overview', icon: Boxes, category: 'Project', action: () => go(`/projects/${projectId}`) },
        { id: 'structure', label: 'Structure', icon: Boxes, category: 'Project', action: () => go(`/projects/${projectId}/structure`) },
        { id: 'delivery', label: 'Delivery', icon: GitBranch, category: 'Project', action: () => go(`/projects/${projectId}/delivery`) },
        { id: 'quality', label: 'Quality', icon: ShieldCheck, category: 'Project', action: () => go(`/projects/${projectId}/quality`) },
        { id: 'audit', label: 'Audit', icon: ScrollText, category: 'Project', action: () => go(`/projects/${projectId}/audit`) },
        { id: 'git', label: 'Git Integration', icon: GitBranch, category: 'Project', action: () => go(`/projects/${projectId}/git`) },
        { id: 'project-settings', label: 'Project Settings', icon: Settings, category: 'Project', action: () => go(`/projects/${projectId}/settings`) },
      ]
    : [];

  const actionCommands: Command[] = [
    { id: 'new-project', label: 'New Project', icon: Plus, shortcut: 'N P', category: 'Actions', action: () => { go('/projects'); setTimeout(() => window.dispatchEvent(new CustomEvent('upcp:action', { detail: 'new-project' })), 100); } },
    ...(projectId
      ? [
          { id: 'new-feature', label: 'New Feature', icon: Plus, shortcut: 'N F', category: 'Actions', action: () => { go(`/projects/${projectId}/delivery`); setTimeout(() => window.dispatchEvent(new CustomEvent('upcp:action', { detail: 'new-feature' })), 100); } },
          { id: 'refresh', label: 'Refresh Data', icon: Zap, shortcut: 'R', category: 'Actions', action: () => { window.dispatchEvent(new CustomEvent('upcp:action', { detail: 'refresh' })); onOpenChange(false); } },
        ]
      : []),
  ];

  const recentIds = getRecentItems();
  const allCommands = [...globalCommands, ...projectCommands, ...actionCommands];
  const recentCommands = recentIds
    .map((id) => allCommands.find((c) => c.id === id))
    .filter(Boolean) as Command[];

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

        {recentCommands.length > 0 && !searchQuery && (
          <>
            <CommandGroup heading="Recent">
              {recentCommands.map((cmd) => (
                <CommandItem
                  key={`recent-${cmd.id}`}
                  value={`recent:${cmd.label}`}
                  onSelect={() => executeCommand(cmd)}
                >
                  <Clock className="mr-2 h-4 w-4 text-muted-foreground" />
                  {cmd.label}
                  {cmd.shortcut && <CommandShortcut>{cmd.shortcut}</CommandShortcut>}
                </CommandItem>
              ))}
            </CommandGroup>
            <CommandSeparator />
          </>
        )}

        <CommandGroup heading="Navigation">
          {globalCommands.map((cmd) => (
            <CommandItem
              key={cmd.id}
              value={cmd.label}
              onSelect={() => executeCommand(cmd)}
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
                  onSelect={() => executeCommand(cmd)}
                >
                  <cmd.icon className="mr-2 h-4 w-4" />
                  {cmd.label}
                </CommandItem>
              ))}
            </CommandGroup>
          </>
        )}

        {actionCommands.length > 0 && (
          <>
            <CommandSeparator />
            <CommandGroup heading="Actions">
              {actionCommands.map((cmd) => (
                <CommandItem
                  key={cmd.id}
                  value={cmd.label}
                  onSelect={() => executeCommand(cmd)}
                >
                  <cmd.icon className="mr-2 h-4 w-4" />
                  {cmd.label}
                  {cmd.shortcut && <CommandShortcut>{cmd.shortcut}</CommandShortcut>}
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
                    onSelect={() => {
                      saveRecentItem(`search:${result.entity_type}:${result.id}`);
                      go(result.url);
                    }}
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
