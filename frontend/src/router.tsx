import { createRouter, createRoute, createRootRoute } from '@tanstack/react-router';
import { AppShell } from '@/components/layouts/AppShell';
import { ProjectList } from '@/components/ProjectList';

const rootRoute = createRootRoute({
  component: AppShell,
});

const indexRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/',
  component: ProjectList,
});

const routeTree = rootRoute.addChildren([indexRoute]);

export const router = createRouter({ routeTree });

declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router;
  }
}