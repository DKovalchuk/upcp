import { Link, useMatches } from '@tanstack/react-router';
import { ChevronRight, Home } from 'lucide-react';

interface BreadcrumbItem {
  path: string;
  title: string;
}

export function BreadcrumbBar() {
  const matches = useMatches();

  const breadcrumbs: BreadcrumbItem[] = matches
    .filter((match) => match.pathname !== '/')
    .map((match) => ({
      path: match.pathname,
      title: match.pathname.split('/').filter(Boolean).pop() || 'Home',
    }));

  if (breadcrumbs.length === 0) {
    return null;
  }

  return (
    <nav className="flex items-center gap-1 px-4 py-2 text-sm text-muted-foreground lg:px-6">
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
