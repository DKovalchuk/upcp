import { useState, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from '@tanstack/react-router';
import {
  Bell,
  CheckCheck,
  Filter,
  Inbox,
  ArrowRight,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { EmptyState } from '@/components/ui/EmptyState';
import { PageSkeleton } from '@/components/ui/PageSkeleton';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  fetchNotifications,
  fetchUnreadCount,
  markNotificationRead,
  markAllNotificationsRead,
} from '@/lib/api';
import { formatRelativeTime } from '@/lib/format';
import { showToast } from '@/lib/toast';
import type { Notification } from '@/types/dashboard';

const NOTIFICATION_TYPES = [
  { value: 'all', label: 'All types' },
  { value: 'task.claimed', label: 'Task Claimed' },
  { value: 'task.status_changed', label: 'Task Status Changed' },
  { value: 'clarification.asked', label: 'Clarification Asked' },
  { value: 'clarification.answered', label: 'Clarification Answered' },
  { value: 'evidence.attached', label: 'Evidence Attached' },
  { value: 'review.completed', label: 'Review Completed' },
  { value: 'review.rejected', label: 'Review Rejected' },
  { value: 'claim.stale', label: 'Stale Claim' },
] as const;

function NotificationRow({
  notification,
  onRead,
  onNavigate,
}: {
  notification: Notification;
  onRead: (id: string) => void;
  onNavigate: (n: Notification) => void;
}) {
  return (
    <div
      className={`flex items-start gap-3 rounded-lg border p-3 transition-colors hover:bg-muted/50 ${
        !notification.is_read ? 'border-l-2 border-l-primary' : ''
      }`}
    >
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <p className="text-sm font-medium leading-tight">{notification.title}</p>
          {!notification.is_read && (
            <span className="h-2 w-2 shrink-0 rounded-full bg-primary" />
          )}
        </div>
        <p className="text-xs text-muted-foreground line-clamp-2 mt-0.5">
          {notification.message}
        </p>
        <div className="flex items-center gap-3 mt-1.5">
          <span className="text-[10px] text-muted-foreground">
            {formatRelativeTime(notification.created_at)}
          </span>
          <span className="rounded bg-muted px-1.5 py-0.5 text-[10px] font-mono text-muted-foreground">
            {notification.type}
          </span>
          {notification.entity_type && (
            <span className="text-[10px] text-muted-foreground">
              {notification.entity_type}
            </span>
          )}
        </div>
      </div>
      <div className="flex shrink-0 items-center gap-1">
        {notification.entity_type && notification.entity_id && (
          <Button
            variant="ghost"
            size="icon"
            className="min-h-[36px] min-w-[36px]"
            onClick={() => onNavigate(notification)}
            aria-label={`Go to ${notification.entity_type}`}
          >
            <ArrowRight className="h-3.5 w-3.5" />
          </Button>
        )}
        {!notification.is_read && (
          <Button
            variant="ghost"
            size="icon"
            className="min-h-[36px] min-w-[36px]"
            onClick={() => onRead(notification.id)}
            aria-label="Mark as read"
          >
            <CheckCheck className="h-3.5 w-3.5" />
          </Button>
        )}
      </div>
    </div>
  );
}

export function NotificationsPage() {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const [typeFilter, setTypeFilter] = useState('all');
  const [readFilter, setReadFilter] = useState<'all' | 'unread'>('all');

  const { data: countData } = useQuery({
    queryKey: ['notifications', 'unread-count'],
    queryFn: fetchUnreadCount,
  });

  const { data, isLoading } = useQuery({
    queryKey: ['notifications'],
    queryFn: () => fetchNotifications(false),
  });

  const markReadMutation = useMutation({
    mutationFn: markNotificationRead,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
    },
    onError: () => {
      showToast.mutationError('update', 'notification');
    },
  });

  const markAllMutation = useMutation({
    mutationFn: markAllNotificationsRead,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
      showToast.updated('All notifications');
    },
    onError: () => {
      showToast.mutationError('update', 'notifications');
    },
  });

  const notifications = data?.items ?? [];
  const unreadCount = countData?.count ?? 0;

  const filteredNotifications = useMemo(() => {
    let result = notifications;
    if (typeFilter !== 'all') {
      result = result.filter((n) => n.type === typeFilter);
    }
    if (readFilter === 'unread') {
      result = result.filter((n) => !n.is_read);
    }
    return result;
  }, [notifications, typeFilter, readFilter]);

  const handleNavigate = (n: Notification) => {
    if (n.entity_type && n.entity_id) {
      if (n.entity_type === 'task') {
        navigate({ to: `/projects` });
      } else if (n.entity_type === 'project') {
        navigate({ to: `/projects/${n.entity_id}` });
      }
    }
  };

  if (isLoading) {
    return <PageSkeleton hasCards rows={6} />;
  }

  return (
    <div className="space-y-[clamp(2rem,4vw,3rem)]">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Bell className="h-5 w-5" />
          <h1 className="text-2xl font-bold tracking-tight">Notifications</h1>
          {unreadCount > 0 && (
            <span className="rounded-full bg-primary px-2 py-0.5 text-xs font-medium text-primary-foreground">
              {unreadCount} unread
            </span>
          )}
        </div>
        {unreadCount > 0 && (
          <Button
            variant="outline"
            size="sm"
            onClick={() => markAllMutation.mutate()}
            disabled={markAllMutation.isPending}
          >
            <CheckCheck className="mr-2 h-3.5 w-3.5" />
            Mark all read
          </Button>
        )}
      </div>

      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2">
          <Filter className="h-4 w-4 text-muted-foreground" />
          <Select value={typeFilter} onValueChange={setTypeFilter}>
            <SelectTrigger className="w-[180px]" aria-label="Filter by type">
              <SelectValue placeholder="All types" />
            </SelectTrigger>
            <SelectContent>
              {NOTIFICATION_TYPES.map((t) => (
                <SelectItem key={t.value} value={t.value}>
                  {t.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div className="flex items-center rounded-md border">
          <Button
            variant={readFilter === 'all' ? 'secondary' : 'ghost'}
            size="sm"
            className="rounded-r-none"
            onClick={() => setReadFilter('all')}
          >
            All
          </Button>
          <Button
            variant={readFilter === 'unread' ? 'secondary' : 'ghost'}
            size="sm"
            className="rounded-l-none"
            onClick={() => setReadFilter('unread')}
          >
            Unread
          </Button>
        </div>
      </div>

      {filteredNotifications.length === 0 ? (
        <EmptyState
          icon={Inbox}
          title="No notifications"
          description={
            typeFilter !== 'all' || readFilter === 'unread'
              ? 'No notifications match your filters.'
              : 'You\'re all caught up!'
          }
        />
      ) : (
        <Card>
          <CardContent className="p-3 space-y-2">
            {filteredNotifications.map((n) => (
              <NotificationRow
                key={n.id}
                notification={n}
                onRead={(id) => markReadMutation.mutate(id)}
                onNavigate={handleNavigate}
              />
            ))}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
