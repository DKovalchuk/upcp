import { createRouter, createRoute, createRootRoute } from '@tanstack/react-router';
import { AppShell } from '@/components/layouts/AppShell';
import { ErrorBoundary } from '@/components/ErrorBoundary';
import React, { Suspense } from 'react';
import { Skeleton } from '@/components/ui/skeleton';

// Lazy-loaded route components
const Dashboard = React.lazy(() =>
  import('@/components/Dashboard').then((module) => ({ default: module.Dashboard }))
);

const ProjectList = React.lazy(() =>
  import('@/components/ProjectList').then((module) => ({ default: module.ProjectList }))
);

const ProjectDetail = React.lazy(() =>
  import('@/components/project/ProjectDetail').then((module) => ({ default: module.ProjectDetail }))
);

const HealthPage = React.lazy(() =>
  import('@/components/HealthPage').then((module) => ({ default: module.HealthPage }))
);

const ReportsPage = React.lazy(() =>
  import('@/components/project/ReportsPage').then((module) => ({ default: module.ReportsPage }))
);

const NotFoundPage = React.lazy(() =>
  import('@/components/NotFoundPage').then((module) => ({ default: module.NotFoundPage }))
);

function RouteLoadingFallback() {
  return (
    <div className="space-y-4">
      <Skeleton className="h-8 w-[200px]" />
      <Skeleton className="h-[400px] w-full" />
    </div>
  );
}

function LazyRoute({ Component }: { Component: React.ComponentType }) {
  return (
    <ErrorBoundary>
      <Suspense fallback={<RouteLoadingFallback />}>
        <Component />
      </Suspense>
    </ErrorBoundary>
  );
}

const rootRoute = createRootRoute({
  component: AppShell,
});

const indexRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/',
  component: () => <LazyRoute Component={Dashboard} />,
});

const projectsRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/projects',
  component: () => <LazyRoute Component={ProjectList} />,
});

const projectDetailRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/projects/$projectId',
  component: () => <LazyRoute Component={ProjectDetail} />,
});

const projectStructureRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/projects/$projectId/structure',
  component: () => <LazyRoute Component={ProjectDetail} />,
});

const projectDeliveryRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/projects/$projectId/delivery',
  component: () => <LazyRoute Component={ProjectDetail} />,
});

const projectQualityRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/projects/$projectId/quality',
  component: () => <LazyRoute Component={ProjectDetail} />,
});

const projectAuditRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/projects/$projectId/audit',
  component: () => <LazyRoute Component={ProjectDetail} />,
});

const projectGitRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/projects/$projectId/git',
  component: () => <LazyRoute Component={ProjectDetail} />,
});

const projectSettingsRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/projects/$projectId/settings',
  component: () => <LazyRoute Component={ProjectDetail} />,
});

const reportsRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/reports',
  component: () => <LazyRoute Component={ReportsPage} />,
});

const healthRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/health',
  component: () => <LazyRoute Component={HealthPage} />,
});

const notFoundRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '*',
  component: () => <LazyRoute Component={NotFoundPage} />,
});

const routeTree = rootRoute.addChildren([
  indexRoute,
  projectsRoute,
  projectDetailRoute,
  projectStructureRoute,
  projectDeliveryRoute,
  projectQualityRoute,
  projectAuditRoute,
  projectGitRoute,
  projectSettingsRoute,
  reportsRoute,
  healthRoute,
  notFoundRoute,
]);

export const router = createRouter({ routeTree });

declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router;
  }
}