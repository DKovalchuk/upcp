import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Bell, CheckCheck, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';
import {
  fetchNotifications,
  fetchUnreadCount,
  markNotificationRead,
  markAllNotificationsRead,
} from '@/lib/api';
import type { Notification } from '@/types/dashboard';
import { formatRelativeTime } from '@/lib/format';

function NotificationItem({
  notification,
  onRead,
}: {
  notification: Notification;
  onRead: () => void;
}) {
  return (
    <DropdownMenuItem
      className={`flex flex-col items-start gap-1 p-3 ${
        !notification.is_read ? 'bg-primary/5' : ''
      }`}
      onClick={() => {
        markNotificationRead(notification.id).then(onRead);
      }}
    >
      <div className="flex w-full items-start justify-between gap-2">
        <p className="text-sm font-medium leading-tight">{notification.title}</p>
        {!notification.is_read && (
          <span className="mt-1 h-2 w-2 shrink-0 rounded-full bg-primary" />
        )}
      </div>
      <p className="text-xs text-muted-foreground line-clamp-2">
        {notification.message}
      </p>
      <p className="text-[10px] text-muted-foreground">
        {formatRelativeTime(notification.created_at)}
      </p>
    </DropdownMenuItem>
  );
}

export function NotificationBell() {
  const queryClient = useQueryClient();
  const [open, setOpen] = useState(false);

  const { data: countData } = useQuery({
    queryKey: ['notifications', 'unread-count'],
    queryFn: fetchUnreadCount,
    refetchInterval: 30000,
    staleTime: 15000,
  });

  const { data: notifData, isLoading } = useQuery({
    queryKey: ['notifications'],
    queryFn: () => fetchNotifications(false),
    enabled: open,
    staleTime: 10000,
  });

  const markAllMutation = useMutation({
    mutationFn: markAllNotificationsRead,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
    },
  });

  const unreadCount = countData?.count ?? 0;
  const notifications = notifData?.items ?? [];

  return (
    <DropdownMenu open={open} onOpenChange={setOpen}>
      <Tooltip>
        <TooltipTrigger
          render={
            <DropdownMenuTrigger asChild>
              <Button
                variant="ghost"
                size="icon"
                className="relative h-8 w-8"
                aria-label={`Notifications (${unreadCount} unread)`}
              />
            </DropdownMenuTrigger>
          }
        >
          <Bell className="h-4 w-4" />
          {unreadCount > 0 && (
            <span className="absolute -right-0.5 -top-0.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-primary px-1 text-[10px] font-medium text-primary-foreground animate-badge-pop">
              {unreadCount > 99 ? '99+' : unreadCount}
            </span>
          )}
        </TooltipTrigger>
        <TooltipContent>Notifications</TooltipContent>
      </Tooltip>

      <DropdownMenuContent align="end" className="w-80 max-h-96 overflow-y-auto">
        <DropdownMenuLabel className="flex items-center justify-between">
          <span>Notifications</span>
          {unreadCount > 0 && (
            <Button
              variant="ghost"
              size="sm"
              className="h-6 text-xs"
              onClick={() => markAllMutation.mutate()}
            >
              <CheckCheck className="mr-1 h-3 w-3" />
              Mark all read
            </Button>
          )}
        </DropdownMenuLabel>
        <DropdownMenuSeparator />

        {isLoading ? (
          <div className="p-4 text-center text-sm text-muted-foreground">
            Loading...
          </div>
        ) : notifications.length === 0 ? (
          <div className="p-4 text-center text-sm text-muted-foreground">
            No notifications
          </div>
        ) : (
          <DropdownMenuGroup>
            {notifications.slice(0, 20).map((n) => (
              <NotificationItem
                key={n.id}
                notification={n}
                onRead={() => {
                  queryClient.invalidateQueries({ queryKey: ['notifications'] });
                }}
              />
            ))}
          </DropdownMenuGroup>
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
