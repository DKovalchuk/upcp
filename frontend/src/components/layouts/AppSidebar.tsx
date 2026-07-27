import { Link, useLocation } from '@tanstack/react-router';
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarRail,
} from '@/components/ui/sidebar';
import { NAV_GROUPS, PROJECT_NAV_GROUP } from '@/lib/constants';
import { useMemo } from 'react';

function isProjectRoute(pathname: string): boolean {
  return /^\/projects\/[^/]+/.test(pathname);
}

export function AppSidebar() {
  const location = useLocation();
  const onProjectRoute = isProjectRoute(location.pathname);

  const projectId = useMemo(() => {
    if (!onProjectRoute) return null;
    const match = location.pathname.match(/^\/projects\/([^/]+)/);
    return match?.[1] ?? null;
  }, [location.pathname, onProjectRoute]);

  return (
    <Sidebar collapsible="icon">
      <SidebarHeader>
        <div className="flex items-center gap-2 px-4 py-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground font-bold text-sm">
            U
          </div>
          <span className="font-semibold text-lg group-data-[collapsible=icon]:hidden">
            UPCP
          </span>
        </div>
      </SidebarHeader>
      <SidebarContent>
        {NAV_GROUPS.map((group) => (
          <SidebarGroup key={group.title}>
            <SidebarGroupLabel>{group.title}</SidebarGroupLabel>
            <SidebarGroupContent>
              <SidebarMenu>
                {group.items.map((item) => {
                  const Icon = item.icon;
                  const isActive = location.pathname === item.path;
                  return (
                    <SidebarMenuItem key={item.path}>
                      <SidebarMenuButton
                        isActive={isActive}
                        tooltip={item.title}
                        render={
                          <Link
                            to={item.path}
                            className="flex items-center gap-2"
                          />
                        }
                      >
                        <Icon className="h-4 w-4" />
                        <span>{item.title}</span>
                      </SidebarMenuButton>
                    </SidebarMenuItem>
                  );
                })}
              </SidebarMenu>
            </SidebarGroupContent>
          </SidebarGroup>
        ))}

        {onProjectRoute && projectId && (
          <SidebarGroup>
            <SidebarGroupLabel>{PROJECT_NAV_GROUP.title}</SidebarGroupLabel>
            <SidebarGroupContent>
              <SidebarMenu>
                {PROJECT_NAV_GROUP.items.map((item) => {
                  const Icon = item.icon;
                  const basePath = `/projects/${projectId}`;
                  const itemPath = item.path
                    ? `${basePath}/${item.path}`
                    : basePath;
                  const isActive = location.pathname === itemPath;
                  return (
                    <SidebarMenuItem key={item.title}>
                      <SidebarMenuButton
                        isActive={isActive}
                        tooltip={item.title}
                        render={
                          <Link
                            to={itemPath}
                            className="flex items-center gap-2"
                          />
                        }
                      >
                        <Icon className="h-4 w-4" />
                        <span>{item.title}</span>
                      </SidebarMenuButton>
                    </SidebarMenuItem>
                  );
                })}
              </SidebarMenu>
            </SidebarGroupContent>
          </SidebarGroup>
        )}
      </SidebarContent>
      <SidebarRail />
    </Sidebar>
  );
}
