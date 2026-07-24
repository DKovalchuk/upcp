import { createRouter, createRoute, createRootRoute } from '@tanstack/react-router';
import { Layout } from '@/components/Layout';
import { ProjectList } from '@/components/ProjectList';

const rootRoute = createRootRoute({
  component: Layout,
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