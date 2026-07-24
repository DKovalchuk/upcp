import { createRouter, createRoute, createRootRoute } from '@tanstack/react-router';
import { AppShell } from '@/components/layouts/AppShell';
import { ErrorBoundary } from '@/components/ErrorBoundary';
import React, { Suspense } from 'react';
import { Skeleton } from '@/components/ui/skeleton';

// Lazy-loaded route components
const ProjectList = React.lazy(() =>
  import('@/components/ProjectList').then((module) => ({ default: module.ProjectList }))
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
  component: () => <LazyRoute Component={ProjectList} />,
});

const projectsRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/projects',
  component: () => <LazyRoute Component={ProjectList} />,
});

const notFoundRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '*',
  component: () => <LazyRoute Component={NotFoundPage} />,
});

const routeTree = rootRoute.addChildren([indexRoute, projectsRoute, notFoundRoute]);

export const router = createRouter({ routeTree });

declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router;
  }
}