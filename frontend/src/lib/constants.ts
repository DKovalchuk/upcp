import {
  LayoutDashboard,
  FolderKanban,
  BarChart3,
  Activity,
  Settings,
  Info,
  Boxes,
  GitBranch,
  ShieldCheck,
  ScrollText,
  Bot,
  TrendingUp,
} from 'lucide-react';
import type { LucideIcon } from 'lucide-react';

export interface NavItem {
  title: string;
  icon: LucideIcon;
  path: string;
  badge?: number;
}

export interface NavGroup {
  title: string;
  items: NavItem[];
}

export const NAV_GROUPS: NavGroup[] = [
  {
    title: 'Main',
    items: [
      { title: 'Dashboard', icon: LayoutDashboard, path: '/' },
      { title: 'Projects', icon: FolderKanban, path: '/projects' },
      { title: 'Agents', icon: Bot, path: '/agents' },
    ],
  },
  {
    title: 'System',
    items: [
      { title: 'Reports', icon: BarChart3, path: '/reports' },
      { title: 'Analytics', icon: TrendingUp, path: '/analytics' },
      { title: 'Health', icon: Activity, path: '/health' },
      { title: 'Settings', icon: Settings, path: '/settings' },
    ],
  },
];

export const PROJECT_NAV_GROUP: NavGroup = {
  title: 'Project',
  items: [
    { title: 'Overview', icon: Info, path: '' },
    { title: 'Structure', icon: Boxes, path: 'structure' },
    { title: 'Delivery', icon: GitBranch, path: 'delivery' },
    { title: 'Quality', icon: ShieldCheck, path: 'quality' },
    { title: 'Audit', icon: ScrollText, path: 'audit' },
    { title: 'Settings', icon: Settings, path: 'settings' },
  ],
};

/* ── Status Colors (semantic, theme-aware) ── */
export const STATUS_COLORS: Record<string, { bg: string; text: string; dot: string }> = {
  active: { bg: 'bg-emerald-500/10 dark:bg-emerald-500/15', text: 'text-emerald-600 dark:text-emerald-400', dot: 'bg-emerald-500' },
  backlog: { bg: 'bg-slate-500/10 dark:bg-slate-500/15', text: 'text-slate-600 dark:text-slate-400', dot: 'bg-slate-500' },
  'in-progress': { bg: 'bg-blue-500/10 dark:bg-blue-500/15', text: 'text-blue-600 dark:text-blue-400', dot: 'bg-blue-500' },
  in_progress: { bg: 'bg-blue-500/10 dark:bg-blue-500/15', text: 'text-blue-600 dark:text-blue-400', dot: 'bg-blue-500' },
  blocked: { bg: 'bg-red-500/10 dark:bg-red-500/15', text: 'text-red-600 dark:text-red-400', dot: 'bg-red-500' },
  done: { bg: 'bg-emerald-500/10 dark:bg-emerald-500/15', text: 'text-emerald-600 dark:text-emerald-400', dot: 'bg-emerald-500' },
  cancelled: { bg: 'bg-gray-500/10 dark:bg-gray-500/15', text: 'text-gray-600 dark:text-gray-400', dot: 'bg-gray-500' },
  paused: { bg: 'bg-amber-500/10 dark:bg-amber-500/15', text: 'text-amber-600 dark:text-amber-400', dot: 'bg-amber-500' },
  archived: { bg: 'bg-gray-500/10 dark:bg-gray-500/15', text: 'text-gray-600 dark:text-gray-400', dot: 'bg-gray-500' },
  ready: { bg: 'bg-blue-500/10 dark:bg-blue-500/15', text: 'text-blue-600 dark:text-blue-400', dot: 'bg-blue-500' },
  needs_clarification: { bg: 'bg-amber-500/10 dark:bg-amber-500/15', text: 'text-amber-600 dark:text-amber-400', dot: 'bg-amber-500' },
  ready_for_review: { bg: 'bg-violet-500/10 dark:bg-violet-500/15', text: 'text-violet-600 dark:text-violet-400', dot: 'bg-violet-500' },
  changes_requested: { bg: 'bg-orange-500/10 dark:bg-orange-500/15', text: 'text-orange-600 dark:text-orange-400', dot: 'bg-orange-500' },
};

/* ── Priority Colors ── */
export const PRIORITY_COLORS: Record<number, { bg: string; text: string; dot: string }> = {
  0: { bg: 'bg-red-500/10 dark:bg-red-500/15', text: 'text-red-600 dark:text-red-400', dot: 'bg-red-500' },
  1: { bg: 'bg-orange-500/10 dark:bg-orange-500/15', text: 'text-orange-600 dark:text-orange-400', dot: 'bg-orange-500' },
  2: { bg: 'bg-amber-500/10 dark:bg-amber-500/15', text: 'text-amber-600 dark:text-amber-400', dot: 'bg-amber-500' },
  3: { bg: 'bg-green-500/10 dark:bg-green-500/15', text: 'text-green-600 dark:text-green-400', dot: 'bg-green-500' },
};

export const PRIORITY_LABELS: Record<number, string> = {
  0: 'Critical',
  1: 'High',
  2: 'Medium',
  3: 'Low',
};

/* ── Agent Status Colors ── */
export const AGENT_STATUS_COLORS: Record<string, { bg: string; text: string; dot: string }> = {
  working: { bg: 'bg-violet-500/10 dark:bg-violet-500/15', text: 'text-violet-600 dark:text-violet-400', dot: 'bg-violet-500' },
  idle: { bg: 'bg-slate-500/10 dark:bg-slate-500/15', text: 'text-slate-600 dark:text-slate-400', dot: 'bg-slate-500' },
  blocked: { bg: 'bg-red-500/10 dark:bg-red-500/15', text: 'text-red-600 dark:text-red-400', dot: 'bg-red-500' },
  offline: { bg: 'bg-gray-500/10 dark:bg-gray-500/15', text: 'text-gray-600 dark:text-gray-400', dot: 'bg-gray-500' },
  stale: { bg: 'bg-amber-500/10 dark:bg-amber-500/15', text: 'text-amber-600 dark:text-amber-400', dot: 'bg-amber-500' },
};

/* ── Actor Type Colors (Agent vs Human vs System) ── */
export const ACTOR_COLORS: Record<string, { bg: string; text: string; border: string }> = {
  agent: { bg: 'bg-violet-500/10', text: 'text-violet-600 dark:text-violet-400', border: 'border-violet-500/20' },
  human: { bg: 'bg-blue-500/10', text: 'text-blue-600 dark:text-blue-400', border: 'border-blue-500/20' },
  system: { bg: 'bg-slate-500/10', text: 'text-slate-600 dark:text-slate-400', border: 'border-slate-500/20' },
};

/* ── Global Hotkeys ── */
export const HOTKEYS = {
  commandPalette: { key: 'k', modifier: 'ctrl' },
  search: { key: '/', modifier: 'ctrl' },
  toggleSidebar: { key: 'b', modifier: 'ctrl' },
  toggleTheme: { key: 'j', modifier: 'ctrl' },
  showShortcuts: { key: '?' },
  dashboard: { key: 'd', sequence: 'g' },
  projects: { key: 'p', sequence: 'g' },
  agents: { key: 'a', sequence: 'g' },
  reports: { key: 'r', sequence: 'g' },
  settings: { key: 's', sequence: 'g' },
} as const;
