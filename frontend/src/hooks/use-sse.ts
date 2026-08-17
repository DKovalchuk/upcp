import { useEffect, useRef, useCallback } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { showToast } from '@/lib/toast';

interface SSENotification {
  event_type: string;
  critical: boolean;
  entity_type?: string;
  entity_id?: string;
  task_title?: string;
  [key: string]: string | boolean | undefined;
}

const RECONNECT_DELAY = 3000;
const MAX_RECONNECT_DELAY = 30000;

export function useSSE(userId: string = 'default') {
  const queryClient = useQueryClient();
  const eventSourceRef = useRef<EventSource | null>(null);
  const reconnectDelay = useRef(RECONNECT_DELAY);

  const connect = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    const url = `/api/v1/notifications/stream?user_id=${encodeURIComponent(userId)}`;
    const es = new EventSource(url);
    eventSourceRef.current = es;

    es.addEventListener('notification', ((event: MessageEvent) => {
      try {
        const data: SSENotification = JSON.parse(event.data);

        // Invalidate notification queries to refresh counts/lists
        queryClient.invalidateQueries({ queryKey: ['notifications'] });

        // Show toast for critical events
        if (data.critical) {
          const title = data.task_title || data.event_type;
          showToast.info(`New: ${title}`);
        }

        // Reset reconnect delay on successful message
        reconnectDelay.current = RECONNECT_DELAY;
      } catch {
        // Ignore parse errors
      }
    }) as EventListener);

    es.onerror = () => {
      es.close();
      // Exponential backoff reconnect
      setTimeout(() => {
        reconnectDelay.current = Math.min(reconnectDelay.current * 2, MAX_RECONNECT_DELAY);
        connect();
      }, reconnectDelay.current);
    };
  }, [userId, queryClient]);

  useEffect(() => {
    connect();
    return () => {
      eventSourceRef.current?.close();
    };
  }, [connect]);

  return {
    isConnected: eventSourceRef.current?.readyState === EventSource.OPEN,
  };
}
