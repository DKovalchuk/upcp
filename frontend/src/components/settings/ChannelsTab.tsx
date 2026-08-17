import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import { Radio, Plus, Trash2, ExternalLink } from 'lucide-react';
import { showToast } from '@/lib/toast';

interface Channel {
  id: string;
  type: 'email' | 'webhook';
  name: string;
  target: string;
  enabled: boolean;
}

const STORAGE_KEY = 'upcp-notification-channels';

function loadChannels(): Channel[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) return JSON.parse(raw);
  } catch { /* ignore */ }
  return [];
}

function saveChannels(channels: Channel[]): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(channels));
}

export function ChannelsTab() {
  const [channels, setChannels] = useState<Channel[]>(loadChannels);
  const [showCreate, setShowCreate] = useState(false);
  const [newChannel, setNewChannel] = useState<{
    type: 'email' | 'webhook';
    name: string;
    target: string;
  }>({ type: 'email', name: '', target: '' });

  const handleCreate = () => {
    if (!newChannel.name.trim() || !newChannel.target.trim()) return;
    const ch: Channel = {
      id: crypto.randomUUID(),
      type: newChannel.type,
      name: newChannel.name.trim(),
      target: newChannel.target.trim(),
      enabled: true,
    };
    const updated = [...channels, ch];
    setChannels(updated);
    saveChannels(updated);
    setNewChannel({ type: 'email', name: '', target: '' });
    setShowCreate(false);
    showToast.created('Channel');
  };

  const handleDelete = (id: string) => {
    const updated = channels.filter((c) => c.id !== id);
    setChannels(updated);
    saveChannels(updated);
    showToast.deleted('Channel');
  };

  const handleToggle = (id: string) => {
    const updated = channels.map((c) =>
      c.id === id ? { ...c, enabled: !c.enabled } : c
    );
    setChannels(updated);
    saveChannels(updated);
  };

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <div className="flex items-center gap-2">
            <Radio className="h-4 w-4" />
            <CardTitle>Notification Channels</CardTitle>
          </div>
          <Button size="sm" onClick={() => setShowCreate(true)}>
            <Plus className="mr-2 h-3.5 w-3.5" />
            Add Channel
          </Button>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground mb-4">
            Configure where notifications are delivered.
          </p>
          {channels.length === 0 ? (
            <div className="rounded-lg border border-dashed p-8 text-center">
              <Radio className="mx-auto h-8 w-8 text-muted-foreground/50 mb-3" />
              <p className="text-sm text-muted-foreground">
                No channels configured. Add a channel to start receiving notifications.
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {channels.map((ch) => (
                <div
                  key={ch.id}
                  className="flex items-center justify-between rounded-lg border p-3"
                >
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium">{ch.name}</span>
                      <span className="rounded bg-muted px-1.5 py-0.5 text-xs font-mono text-muted-foreground">
                        {ch.type}
                      </span>
                    </div>
                    <p className="text-xs text-muted-foreground truncate mt-0.5">
                      {ch.target}
                    </p>
                  </div>
                  <div className="flex items-center gap-1">
                    <button
                      type="button"
                      role="switch"
                      aria-checked={ch.enabled}
                      aria-label={`Toggle ${ch.name}`}
                      onClick={() => handleToggle(ch.id)}
                      className={`relative inline-flex h-5 w-9 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring ${
                        ch.enabled ? 'bg-primary' : 'bg-input'
                      }`}
                    >
                      <span
                        className={`pointer-events-none inline-block h-4 w-4 rounded-full bg-background shadow-sm transition-transform ${
                          ch.enabled ? 'translate-x-4' : 'translate-x-0'
                        }`}
                      />
                    </button>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="min-h-[36px] min-w-[36px] text-destructive"
                      onClick={() => handleDelete(ch.id)}
                      aria-label={`Delete channel ${ch.name}`}
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      <Dialog open={showCreate} onOpenChange={setShowCreate}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Add Notification Channel</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium" htmlFor="channel-type">Type</label>
              <div className="flex gap-2 mt-1.5">
                <Button
                  variant={newChannel.type === 'email' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setNewChannel((p) => ({ ...p, type: 'email' }))}
                >
                  Email
                </Button>
                <Button
                  variant={newChannel.type === 'webhook' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setNewChannel((p) => ({ ...p, type: 'webhook' }))}
                >
                  Webhook
                </Button>
              </div>
            </div>
            <div>
              <label className="text-sm font-medium" htmlFor="channel-name">Name</label>
              <Input
                id="channel-name"
                placeholder="e.g. DevOps alerts"
                value={newChannel.name}
                onChange={(e) =>
                  setNewChannel((p) => ({ ...p, name: e.target.value }))
                }
                className="mt-1.5"
              />
            </div>
            <div>
              <label className="text-sm font-medium" htmlFor="channel-target">
                {newChannel.type === 'email' ? 'Email Address' : 'Webhook URL'}
              </label>
              <Input
                id="channel-target"
                placeholder={
                  newChannel.type === 'email'
                    ? 'alerts@example.com'
                    : 'https://hooks.slack.com/...'
                }
                value={newChannel.target}
                onChange={(e) =>
                  setNewChannel((p) => ({ ...p, target: e.target.value }))
                }
                className="mt-1.5"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCreate(false)}>
              Cancel
            </Button>
            <Button
              onClick={handleCreate}
              disabled={!newChannel.name.trim() || !newChannel.target.trim()}
            >
              <ExternalLink className="mr-2 h-3.5 w-3.5" />
              Add Channel
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
