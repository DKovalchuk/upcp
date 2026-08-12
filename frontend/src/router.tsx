/* oxlint-disable react/only-export-components */
import { createRouter, createRoute, createRootRoute, Navigate } from '@tanstack/react-router';
import { AppShell } from '@/components/layouts/AppShell';
import { ErrorBoundary } from '@/components/ErrorBoundary';
import { AuthProvider, useAuth } from '@/contexts/AuthContext';
import { SSEProvider } from '@/components/SSEProvider';
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

const SettingsPage = React.lazy(() =>
  import('@/components/SettingsPage').then((module) => ({ default: module.SettingsPage }))
);

const NotificationsPage = React.lazy(() =>
  import('@/components/notifications/NotificationsPage').then((module) => ({ default: module.NotificationsPage }))
);

const AnalyticsPage = React.lazy(() =>
  import('@/components/analytics/AnalyticsPage').then((module) => ({ default: module.AnalyticsPage }))
);

const AgentCenterPage = React.lazy(() =>
  import('@/pages/AgentCenterPage').then((module) => ({ default: module.AgentCenterPage }))
);

const AgentDetailPage = React.lazy(() =>
  import('@/pages/AgentDetailPage').then((module) => ({ default: module.AgentDetailPage }))
);

const NotFoundPage = React.lazy(() =>
  import('@/components/NotFoundPage').then((module) => ({ default: module.NotFoundPage }))
);

const LoginPage = React.lazy(() =>
  import('@/components/auth/LoginPage').then((module) => ({ default: module.LoginPage }))
);

const SetupPage = React.lazy(() =>
  import('@/components/auth/SetupPage').then((module) => ({ default: module.SetupPage }))
);

// eslint-disable-next-line react/only-export-components
function RouteLoadingFallback() {
  return (
    <div className="space-y-4">
      <Skeleton className="h-8 w-[200px]" />
      <Skeleton className="h-[400px] w-full" />
    </div>
  );
}

// eslint-disable-next-line react/only-export-components
function LazyRoute({ Component }: { Component: React.ComponentType }) {
  return (
    <ErrorBoundary>
      <Suspense fallback={<RouteLoadingFallback />}>
        <Component />
      </Suspense>
    </ErrorBoundary>
  );
}

// Auth guard - redirects to /login if not authenticated
// eslint-disable-next-line react/only-export-components
function AuthGuard({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return <RouteLoadingFallback />;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
}

// Root route with AuthProvider
const rootRoute = createRootRoute({
  component: () => (
    <AuthProvider>
      <SSEProvider>
        <AppShell />
      </SSEProvider>
    </AuthProvider>
  ),
});

// Auth routes (no guard)
const loginRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/login',
  component: () => <LazyRoute Component={LoginPage} />,
});

const setupRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/setup',
  component: () => <LazyRoute Component={SetupPage} />,
});

// Protected routes (with guard)
const indexRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/',
  component: () => (
    <AuthGuard>
      <LazyRoute Component={Dashboard} />
    </AuthGuard>
  ),
});

const projectsRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/projects',
  component: () => (
    <AuthGuard>
      <LazyRoute Component={ProjectList} />
    </AuthGuard>
  ),
});

const projectDetailRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/projects/$projectId',
  component: () => (
    <AuthGuard>
      <LazyRoute Component={ProjectDetail} />
    </AuthGuard>
  ),
});

const projectStructureRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/projects/$projectId/structure',
  component: () => (
    <AuthGuard>
      <LazyRoute Component={ProjectDetail} />
    </AuthGuard>
  ),
});

const projectDeliveryRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/projects/$projectId/delivery',
  component: () => (
    <AuthGuard>
      <LazyRoute Component={ProjectDetail} />
    </AuthGuard>
  ),
});

const projectQualityRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/projects/$projectId/quality',
  component: () => (
    <AuthGuard>
      <LazyRoute Component={ProjectDetail} />
    </AuthGuard>
  ),
});

const projectAuditRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/projects/$projectId/audit',
  component: () => (
    <AuthGuard>
      <LazyRoute Component={ProjectDetail} />
    </AuthGuard>
  ),
});

const projectGitRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/projects/$projectId/git',
  component: () => (
    <AuthGuard>
      <LazyRoute Component={ProjectDetail} />
    </AuthGuard>
  ),
});

const projectSettingsRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/projects/$projectId/settings',
  component: () => (
    <AuthGuard>
      <LazyRoute Component={ProjectDetail} />
    </AuthGuard>
  ),
});

const reportsRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/reports',
  component: () => (
    <AuthGuard>
      <LazyRoute Component={ReportsPage} />
    </AuthGuard>
  ),
});

const settingsRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/settings',
  component: () => (
    <AuthGuard>
      <LazyRoute Component={SettingsPage} />
    </AuthGuard>
  ),
});

const healthRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/health',
  component: () => <LazyRoute Component={HealthPage} />,
});

const agentsRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/agents',
  component: () => (
    <AuthGuard>
      <LazyRoute Component={AgentCenterPage} />
    </AuthGuard>
  ),
});

const agentDetailRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/agents/$agentId',
  component: () => (
    <AuthGuard>
      <LazyRoute Component={AgentDetailPage} />
    </AuthGuard>
  ),
});

const analyticsRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/analytics',
  component: () => (
    <AuthGuard>
      <LazyRoute Component={AnalyticsPage} />
    </AuthGuard>
  ),
});

const notificationsRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/notifications',
  component: () => (
    <AuthGuard>
      <LazyRoute Component={NotificationsPage} />
    </AuthGuard>
  ),
});

const notFoundRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '*',
  component: () => <LazyRoute Component={NotFoundPage} />,
});

const routeTree = rootRoute.addChildren([
  loginRoute,
  setupRoute,
  indexRoute,
  projectsRoute,
  projectDetailRoute,
  projectStructureRoute,
  projectDeliveryRoute,
  projectQualityRoute,
  projectAuditRoute,
  projectGitRoute,
  projectSettingsRoute,
  agentsRoute,
  agentDetailRoute,
  reportsRoute,
  settingsRoute,
  analyticsRoute,
  notificationsRoute,
  healthRoute,
  notFoundRoute,
]);

// eslint-disable-next-line react/only-export-components
export const router = createRouter({ routeTree });

declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router;
  }
}
