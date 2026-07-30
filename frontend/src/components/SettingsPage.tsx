import { useTheme } from 'next-themes';
import { useHealth } from '@/hooks/use-health';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Settings, Palette, Server, Info, Sun, Moon, Monitor, CheckCircle, XCircle } from 'lucide-react';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1';
const APP_VERSION = '0.14.0';

function ThemeToggle() {
  const { theme, setTheme } = useTheme();

  return (
    <div className="flex items-center gap-2">
      <Button
        variant={theme === 'light' ? 'default' : 'outline'}
        size="sm"
        onClick={() => setTheme('light')}
      >
        <Sun className="h-4 w-4 mr-2" />
        Light
      </Button>
      <Button
        variant={theme === 'dark' ? 'default' : 'outline'}
        size="sm"
        onClick={() => setTheme('dark')}
      >
        <Moon className="h-4 w-4 mr-2" />
        Dark
      </Button>
      <Button
        variant={theme === 'system' ? 'default' : 'outline'}
        size="sm"
        onClick={() => setTheme('system')}
      >
        <Monitor className="h-4 w-4 mr-2" />
        System
      </Button>
    </div>
  );
}

export function SettingsPage() {
  const { data: health } = useHealth();

  return (
    <div className="space-y-[clamp(4rem,8vw,6rem)]">
      <div className="flex items-center gap-2">
        <Settings className="h-5 w-5" />
        <h1 className="text-2xl font-bold tracking-tight">Settings</h1>
      </div>

      <section>
        <Card>
          <CardHeader className="flex flex-row items-center gap-2 space-y-0 pb-2">
            <Palette className="h-4 w-4" />
            <CardTitle>Appearance</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground mb-4">
              Choose your preferred color scheme. Changes apply immediately.
            </p>
            <ThemeToggle />
          </CardContent>
        </Card>
      </section>

      <section>
        <Card>
          <CardHeader className="flex flex-row items-center gap-2 space-y-0 pb-2">
            <Server className="h-4 w-4" />
            <CardTitle>API Information</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <p className="text-sm font-medium">API Base URL</p>
                <p className="text-sm text-muted-foreground font-mono">{API_BASE_URL}</p>
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
                      {health.latency_ms !== undefined && (
                        <span className="text-xs text-muted-foreground">{health.latency_ms}ms</span>
                      )}
                    </>
                  ) : (
                    <span className="text-sm text-muted-foreground">Checking...</span>
                  )}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </section>

      <section>
        <Card>
          <CardHeader className="flex flex-row items-center gap-2 space-y-0 pb-2">
            <Info className="h-4 w-4" />
            <CardTitle>About</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div>
                <p className="text-sm font-medium">Application</p>
                <p className="text-sm text-muted-foreground">UPCP — Universal Project Control Plane</p>
              </div>
              <div>
                <p className="text-sm font-medium">Version</p>
                <p className="text-sm text-muted-foreground font-mono">{APP_VERSION}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </section>
    </div>
  );
}
