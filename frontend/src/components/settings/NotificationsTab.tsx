import { useState, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Bell, Save } from 'lucide-react';
import { showToast } from '@/lib/toast';

const EVENT_TYPES = [
  { key: 'task.created', label: 'Task Created', description: 'When a new task is created' },
  { key: 'task.status_changed', label: 'Task Status Changed', description: 'When a task moves between states' },
  { key: 'task.claimed', label: 'Task Claimed', description: 'When an agent claims a task' },
  { key: 'task.completed', label: 'Task Completed', description: 'When a task is marked done' },
  { key: 'evidence.attached', label: 'Evidence Attached', description: 'When evidence is added to a task' },
  { key: 'review.completed', label: 'Review Completed', description: 'When a review round finishes' },
  { key: 'clarification.asked', label: 'Clarification Asked', description: 'When a clarification is requested' },
  { key: 'claim.stale', label: 'Stale Claim', description: 'When an agent claim expires' },
] as const;

const STORAGE_KEY = 'upcp-notification-preferences';

function loadPreferences(): Record<string, boolean> {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) return JSON.parse(raw);
  } catch { /* ignore */ }
  const defaults: Record<string, boolean> = {};
  for (const et of EVENT_TYPES) {
    defaults[et.key] = true;
  }
  return defaults;
}

function savePreferences(prefs: Record<string, boolean>): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(prefs));
}

function Toggle({
  checked,
  onToggle,
  label,
}: {
  checked: boolean;
  onToggle: () => void;
  label: string;
}) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      aria-label={label}
      onClick={onToggle}
      className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background ${
        checked ? 'bg-primary' : 'bg-input'
      }`}
    >
      <span
        className={`pointer-events-none inline-block h-5 w-5 rounded-full bg-background shadow-lg transition-transform ${
          checked ? 'translate-x-5' : 'translate-x-0'
        }`}
      />
    </button>
  );
}

export function NotificationsTab() {
  const [prefs, setPrefs] = useState<Record<string, boolean>>(loadPreferences);
  const [hasChanges, setHasChanges] = useState(false);

  const toggle = useCallback((key: string) => {
    setPrefs((prev) => ({ ...prev, [key]: !prev[key] }));
    setHasChanges(true);
  }, []);

  const handleSave = () => {
    savePreferences(prefs);
    setHasChanges(false);
    showToast.updated('Notification preferences');
  };

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <div className="flex items-center gap-2">
            <Bell className="h-4 w-4" />
            <CardTitle>Notification Preferences</CardTitle>
          </div>
          {hasChanges && (
            <Button size="sm" onClick={handleSave}>
              <Save className="mr-2 h-3.5 w-3.5" />
              Save
            </Button>
          )}
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground mb-4">
            Choose which events generate notifications. Changes are local to this browser.
          </p>
          <div className="space-y-4">
            {EVENT_TYPES.map((et) => (
              <div key={et.key} className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium">{et.label}</p>
                  <p className="text-xs text-muted-foreground">{et.description}</p>
                </div>
                <Toggle
                  checked={prefs[et.key] ?? true}
                  onToggle={() => toggle(et.key)}
                  label={`Toggle ${et.label}`}
                />
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
