import { Link, useMatches } from '@tanstack/react-router';
import { ChevronRight, Home } from 'lucide-react';

interface BreadcrumbItem {
  path: string;
  title: string;
}

const SEGMENT_LABELS: Record<string, string> = {
  projects: 'Projects',
  structure: 'Structure',
  delivery: 'Delivery',
  quality: 'Quality',
  audit: 'Audit',
  git: 'Git',
  settings: 'Settings',
  health: 'Health',
  reports: 'Reports',
};

function isUuid(s: string): boolean {
  return /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(s);
}

function buildBreadcrumbs(pathname: string): BreadcrumbItem[] {
  const segments = pathname.split('/').filter(Boolean);
  const crumbs: BreadcrumbItem[] = [];
  let builtPath = '';

  for (const seg of segments) {
    builtPath += `/${seg}`;
    if (isUuid(seg)) {
      continue;
    }
    const label = SEGMENT_LABELS[seg] ?? seg.charAt(0).toUpperCase() + seg.slice(1);
    crumbs.push({ path: builtPath, title: label });
  }

  return crumbs;
}

export function BreadcrumbBar() {
  const matches = useMatches();
  const lastMatch = matches[matches.length - 1];
  const pathname = lastMatch?.pathname ?? '/';

  if (pathname === '/') return null;

  const breadcrumbs = buildBreadcrumbs(pathname);

  return (
    <nav className="flex items-center gap-1 px-4 py-2 text-sm text-muted-foreground lg:px-6" aria-label="Breadcrumb">
      <Link to="/" className="flex items-center gap-1 hover:text-foreground">
        <Home className="h-4 w-4" />
        <span>Home</span>
      </Link>
      {breadcrumbs.map((crumb) => (
        <span key={crumb.path} className="flex items-center gap-1">
          <ChevronRight className="h-4 w-4" />
          <Link
            to={crumb.path}
            className="hover:text-foreground capitalize"
          >
            {crumb.title}
          </Link>
        </span>
      ))}
    </nav>
  );
}
