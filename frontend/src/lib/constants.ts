import {
  LayoutDashboard,
  FolderKanban,
  BarChart3,
  Activity,
  Settings,
  ListTodo,
  Layers,
  GitBranch,
  FileText,
} from 'lucide-react';
import type { LucideIcon } from 'lucide-react';

export interface NavItem {
  title: string;
  icon: LucideIcon;
  path: string;
}

export interface NavGroup {
  title: string;
  items: NavItem[];
}

export const NAV_GROUPS: NavGroup[] = [
  {
    title: 'Main',
    items: [
      {
        title: 'Dashboard',
        icon: LayoutDashboard,
        path: '/',
      },
      {
        title: 'Projects',
        icon: FolderKanban,
        path: '/projects',
      },
    ],
  },
  {
    title: 'System',
    items: [
      {
        title: 'Reports',
        icon: BarChart3,
        path: '/reports',
      },
      {
        title: 'Health',
        icon: Activity,
        path: '/health',
      },
      {
        title: 'Settings',
        icon: Settings,
        path: '/settings',
      },
    ],
  },
];

/** Project-specific nav items shown when on /projects/:id/* */
export const PROJECT_NAV_GROUP: NavGroup = {
  title: 'Project',
  items: [
    {
      title: 'Overview',
      icon: Layers,
      path: '', // Will be resolved relative to project
    },
    {
      title: 'Tasks',
      icon: ListTodo,
      path: '',
    },
    {
      title: 'Features',
      icon: GitBranch,
      path: '',
    },
    {
      title: 'Docs',
      icon: FileText,
      path: '',
    },
  ],
};

export const STATUS_COLORS: Record<string, { bg: string; text: string }> = {
  active: { bg: 'bg-emerald-500/10', text: 'text-emerald-600' },
  backlog: { bg: 'bg-slate-500/10', text: 'text-slate-600' },
  'in-progress': { bg: 'bg-blue-500/10', text: 'text-blue-600' },
  paused: { bg: 'bg-amber-500/10', text: 'text-amber-600' },
  archived: { bg: 'bg-red-500/10', text: 'text-red-600' },
  done: { bg: 'bg-violet-500/10', text: 'text-violet-600' },
};

export const PRIORITY_COLORS: Record<string, string> = {
  P0: 'bg-red-500',
  P1: 'bg-orange-500',
  P2: 'bg-yellow-500',
  P3: 'bg-green-500',
};

export const PRIORITY_LABELS: Record<string, string> = {
  P0: 'Critical',
  P1: 'High',
  P2: 'Medium',
  P3: 'Low',
};
