import { useHealth } from '@/hooks/use-health';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Info, Server, CheckCircle, XCircle } from 'lucide-react';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1';
const APP_VERSION = import.meta.env.VITE_APP_VERSION || '0.21.0';

export function AboutTab() {
  const { data: health } = useHealth();

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader className="flex flex-row items-center gap-2 space-y-0 pb-2">
          <Info className="h-4 w-4" />
          <CardTitle>About</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div>
              <p className="text-sm font-medium">Application</p>
              <p className="text-sm text-muted-foreground">
                UPCP — Universal Project Control Plane
              </p>
            </div>
            <div>
              <p className="text-sm font-medium">Version</p>
              <p className="text-sm text-muted-foreground font-mono">
                {APP_VERSION}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center gap-2 space-y-0 pb-2">
          <Server className="h-4 w-4" />
          <CardTitle>System Health</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div>
              <p className="text-sm font-medium">API Base URL</p>
              <p className="text-sm text-muted-foreground font-mono">
                {API_BASE_URL}
              </p>
            </div>
            <div>
              <p className="text-sm font-medium">Backend Status</p>
              <div className="flex items-center gap-2 mt-1">
                {health ? (
                  <>
                    {health.status === 'ok' ? (
                      <CheckCircle className="h-4 w-4 text-emerald-500" />
                    ) : (
                      <XCircle className="h-4 w-4 text-red-500" />
                    )}
                    <span className="text-sm">
                      {health.status === 'ok' ? 'Connected' : 'Disconnected'}
                    </span>
                    {health.db?.latency_ms !== undefined && (
                      <span className="text-xs text-muted-foreground">
                        {health.db.latency_ms}ms
                      </span>
                    )}
                  </>
                ) : (
                  <span className="text-sm text-muted-foreground">
                    Checking...
                  </span>
                )}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
