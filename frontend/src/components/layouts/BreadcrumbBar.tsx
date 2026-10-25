import { Link, useMatches } from '@tanstack/react-router';
import { ChevronRight, Home } from 'lucide-react';
import { useProject } from '@/hooks/use-projects';

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

function buildBreadcrumbs(pathname: string, projectLabel?: string): BreadcrumbItem[] {
  const segments = pathname.split('/').filter(Boolean);
  const crumbs: BreadcrumbItem[] = [];
  let builtPath = '';
  let prevSeg = '';

  for (const seg of segments) {
    builtPath += `/${seg}`;
    if (isUuid(seg)) {
      // Only `/projects/<uuid>` is a project segment; other uuids (agents,
      // …) must not render a project crumb nor trigger a wrong-entity fetch
      // (regression TASK-0159: /api/v1/projects/<agentId> -> 404).
      if (prevSeg === 'projects') {
        crumbs.push({ path: builtPath, title: projectLabel ?? 'Project' });
      }
      prevSeg = seg;
      continue;
    }
    const label = SEGMENT_LABELS[seg] ?? seg.charAt(0).toUpperCase() + seg.slice(1);
    crumbs.push({ path: builtPath, title: label });
    prevSeg = seg;
  }

  return crumbs;
}

function projectIdFrom(pathname: string): string {
  const segments = pathname.split('/').filter(Boolean);
  const idx = segments.indexOf('projects');
  const candidate = idx === -1 ? '' : (segments[idx + 1] ?? '');
  return isUuid(candidate) ? candidate : '';
}

export function BreadcrumbBar() {
  const matches = useMatches();
  const lastMatch = matches[matches.length - 1];
  const pathname = lastMatch?.pathname ?? '/';

  const projectId = projectIdFrom(pathname);
  const { data: project } = useProject(projectId);

  if (pathname === '/') return null;

  const breadcrumbs = buildBreadcrumbs(pathname, project?.name);

  return (
    <nav className="flex items-center gap-1 px-4 py-2 text-sm text-muted-foreground lg:px-6" aria-label="Breadcrumb">
      <ol className="flex items-center gap-1">
        <li>
          <Link to="/" className="flex items-center gap-1 hover:text-foreground">
            <Home className="h-4 w-4" aria-hidden="true" />
            <span>Home</span>
          </Link>
        </li>
        {breadcrumbs.map((crumb, index) => {
          const isLast = index === breadcrumbs.length - 1;
          return (
            <li key={crumb.path} className="flex items-center gap-1">
              <ChevronRight className="h-4 w-4" aria-hidden="true" />
              {isLast ? (
                <span aria-current="page" className="font-medium text-foreground">
                  {crumb.title}
                </span>
              ) : (
                <Link to={crumb.path} className="hover:text-foreground capitalize">
                  {crumb.title}
                </Link>
              )}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
