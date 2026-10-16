import { useEffect, useRef, useCallback, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { showToast } from '@/lib/toast';
import { safeStorage } from '@/lib/storage';

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

function getToken(): string | null {
  return safeStorage.getItem('upcp_access_token');
}

function parseSSELine(line: string): { event?: string; data?: string } | null {
  if (line.startsWith('event:')) return { event: line.slice(6).trim() };
  if (line.startsWith('data:')) return { data: line.slice(5).trim() };
  if (line === '') return null; // empty line = dispatch boundary
  return null;
}

export function useSSE(userId: string = 'default') {
  const queryClient = useQueryClient();
  const abortRef = useRef<AbortController | null>(null);
  const reconnectDelay = useRef(RECONNECT_DELAY);
  const [isConnected, setIsConnected] = useState(false);

  const connect = useCallback(() => {
    abortRef.current?.abort();

    const url = `/api/v1/notifications/stream?user_id=${encodeURIComponent(userId)}`;
    const token = getToken();

    const headers: Record<string, string> = {};
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const controller = new AbortController();
    abortRef.current = controller;

    fetch(url, { headers, signal: controller.signal })
      .then(async (response) => {
        if (!response.ok) throw new Error(`SSE ${response.status}`);
        setIsConnected(true);
        reconnectDelay.current = RECONNECT_DELAY;

        const reader = response.body?.getReader();
        if (!reader) throw new Error('No readable stream');

        const decoder = new TextDecoder();
        let buffer = '';
        let eventType = '';

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop() ?? '';

          for (const line of lines) {
            const parsed = parseSSELine(line);
            if (parsed?.event) {
              eventType = parsed.event;
            } else if (parsed?.data && eventType === 'notification') {
              try {
                const data: SSENotification = JSON.parse(parsed.data);
                queryClient.invalidateQueries({ queryKey: ['notifications'] });
                queryClient.invalidateQueries({ queryKey: ['dashboard-stats'] });
                queryClient.invalidateQueries({ queryKey: ['attention-dashboard'] });
                if (data.critical) {
                  const title = data.task_title || data.event_type;
                  showToast.info(`New: ${title}`);
                }
              } catch {
                // Ignore parse errors
              }
              eventType = '';
            } else if (line === '') {
              eventType = ''; // reset on dispatch boundary
            }
          }
        }
      })
      .catch((err) => {
        if (err.name === 'AbortError') return;
        setIsConnected(false);
        setTimeout(() => {
          reconnectDelay.current = Math.min(reconnectDelay.current * 2, MAX_RECONNECT_DELAY);
          connect();
        }, reconnectDelay.current);
      });
  }, [userId, queryClient]);

  useEffect(() => {
    connect();
    return () => {
      abortRef.current?.abort();
    };
  }, [connect]);

  return { isConnected };
}
