import { useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
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
import { Radio, Plus, Trash2, ExternalLink, Pencil } from 'lucide-react';
import { showToast } from '@/lib/toast';
import { useNotificationChannels } from '@/hooks/use-analytics';
import {
  createNotificationChannel,
  deleteNotificationChannel,
  toggleNotificationChannel,
  testNotificationChannel,
  updateNotificationChannel,
} from '@/lib/api/analytics';

interface EditingChannel {
  id: string;
  channel_type: string;
  name: string;
  target: string;
  config: Record<string, unknown>;
}

function targetFromConfig(
  channelType: string,
  config: Record<string, unknown>
): string {
  const value = channelType === 'email' ? config.to_address : config.url;
  return typeof value === 'string' ? value : '';
}

export function ChannelsSettingsTab() {
  const queryClient = useQueryClient();
  const { data, isLoading } = useNotificationChannels();
  const channels = data?.items ?? [];
  const [showCreate, setShowCreate] = useState(false);
  const [editing, setEditing] = useState<EditingChannel | null>(null);
  const [newChannel, setNewChannel] = useState<{
    channel_type: string;
    name: string;
    target: string;
  }>({ channel_type: 'email', name: '', target: '' });

  const invalidateChannels = () =>
    queryClient.invalidateQueries({ queryKey: ['notification-channels'] });

  const handleCreate = async () => {
    if (!newChannel.name.trim() || !newChannel.target.trim()) return;
    const config = newChannel.channel_type === 'email'
      ? { smtp_host: 'smtp.example.com', smtp_port: 587, from_address: 'noreply@example.com', to_address: newChannel.target }
      : { url: newChannel.target };
    try {
      await createNotificationChannel({ channel_type: newChannel.channel_type, name: newChannel.name, config });
      invalidateChannels();
      setNewChannel({ channel_type: 'email', name: '', target: '' });
      setShowCreate(false);
      showToast.created('Channel');
    } catch {
      showToast.mutationError('create', 'channel');
    }
  };

  const handleEditSave = async () => {
    if (!editing || !editing.name.trim() || !editing.target.trim()) return;
    const config: Record<string, unknown> = {
      ...editing.config,
      ...(editing.channel_type === 'email'
        ? { to_address: editing.target }
        : { url: editing.target }),
    };
    try {
      await updateNotificationChannel(editing.id, { name: editing.name, config });
      invalidateChannels();
      setEditing(null);
      showToast.updated('Channel');
    } catch {
      showToast.mutationError('update', 'channel');
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await deleteNotificationChannel(id);
      invalidateChannels();
      showToast.deleted('Channel');
    } catch {
      showToast.mutationError('delete', 'channel');
    }
  };

  const handleToggle = async (id: string) => {
    try {
      await toggleNotificationChannel(id);
      invalidateChannels();
    } catch {
      showToast.mutationError('update', 'channel');
    }
  };

  const handleTest = async (id: string) => {
    try {
      await testNotificationChannel(id);
      showToast.updated('Test notification');
    } catch {
      showToast.mutationError('update', 'channel');
    }
  };

  return (
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
        {isLoading ? (
          <div className="h-20 w-full animate-pulse rounded bg-muted" />
        ) : channels.length === 0 ? (
          <div className="rounded-lg border border-dashed p-8 text-center">
            <Radio className="mx-auto h-8 w-8 text-muted-foreground/50 mb-3" />
            <p className="text-sm text-muted-foreground">
              No channels configured. Add a channel to receive notifications.
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {channels.map((ch) => (
              <div key={ch.id} className="flex items-center justify-between rounded-lg border p-3">
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium">{ch.name}</span>
                    <span className="rounded bg-muted px-1.5 py-0.5 text-xs font-mono text-muted-foreground">
                      {ch.channel_type}
                    </span>
                  </div>
                </div>
                <div className="flex items-center gap-1">
                  <Button
                    variant="ghost"
                    size="icon"
                    className="min-h-[36px] min-w-[36px]"
                    aria-label={`Edit channel ${ch.name}`}
                    onClick={() =>
                      setEditing({
                        id: ch.id,
                        channel_type: ch.channel_type,
                        name: ch.name,
                        target: targetFromConfig(ch.channel_type, ch.config),
                        config: ch.config,
                      })
                    }
                  >
                    <Pencil className="h-3.5 w-3.5" />
                  </Button>
                  <Button variant="ghost" size="sm" onClick={() => handleTest(ch.id)}>
                    <ExternalLink className="h-3.5 w-3.5" />
                  </Button>
                  <button
                    type="button"
                    role="switch"
                    aria-checked={ch.is_active}
                    aria-label={`Toggle ${ch.name}`}
                    onClick={() => handleToggle(ch.id)}
                    className={`relative inline-flex h-5 w-9 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors ${
                      ch.is_active ? 'bg-primary' : 'bg-input'
                    }`}
                  >
                    <span className={`pointer-events-none inline-block h-4 w-4 rounded-full bg-background shadow-sm transition-transform ${
                      ch.is_active ? 'translate-x-4' : 'translate-x-0'
                    }`} />
                  </button>
                  <Button variant="ghost" size="icon" className="min-h-[36px] min-w-[36px] text-destructive" onClick={() => handleDelete(ch.id)} aria-label={`Delete channel ${ch.name}`}>
                    <Trash2 className="h-3.5 w-3.5" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>

      <Dialog open={showCreate} onOpenChange={setShowCreate}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Add Notification Channel</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium" htmlFor="ch-type">Type</label>
              <div className="flex gap-2 mt-1.5">
                <Button variant={newChannel.channel_type === 'email' ? 'default' : 'outline'} size="sm" onClick={() => setNewChannel((p) => ({ ...p, channel_type: 'email' }))}>Email</Button>
                <Button variant={newChannel.channel_type === 'webhook' ? 'default' : 'outline'} size="sm" onClick={() => setNewChannel((p) => ({ ...p, channel_type: 'webhook' }))}>Webhook</Button>
              </div>
            </div>
            <div>
              <label className="text-sm font-medium" htmlFor="ch-name">Name</label>
              <Input id="ch-name" placeholder="e.g. DevOps alerts" value={newChannel.name} onChange={(e) => setNewChannel((p) => ({ ...p, name: e.target.value }))} className="mt-1.5" />
            </div>
            <div>
              <label className="text-sm font-medium" htmlFor="ch-target">
                {newChannel.channel_type === 'email' ? 'Email Address' : 'Webhook URL'}
              </label>
              <Input id="ch-target" placeholder={newChannel.channel_type === 'email' ? 'alerts@example.com' : 'https://hooks.slack.com/...'} value={newChannel.target} onChange={(e) => setNewChannel((p) => ({ ...p, target: e.target.value }))} className="mt-1.5" />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCreate(false)}>Cancel</Button>
            <Button onClick={handleCreate} disabled={!newChannel.name.trim() || !newChannel.target.trim()}>Add Channel</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={!!editing} onOpenChange={(open) => { if (!open) setEditing(null); }}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Edit Notification Channel</DialogTitle>
          </DialogHeader>
          {editing && (
            <div className="space-y-4">
              <div>
                <span className="text-sm font-medium">Type</span>
                <span className="ml-2 rounded bg-muted px-1.5 py-0.5 text-xs font-mono text-muted-foreground">
                  {editing.channel_type}
                </span>
              </div>
              <div>
                <label className="text-sm font-medium" htmlFor="ch-edit-name">Name</label>
                <Input
                  id="ch-edit-name"
                  value={editing.name}
                  onChange={(e) => setEditing((p) => (p ? { ...p, name: e.target.value } : p))}
                  className="mt-1.5"
                />
              </div>
              <div>
                <label className="text-sm font-medium" htmlFor="ch-edit-target">
                  {editing.channel_type === 'email' ? 'Email Address' : 'Webhook URL'}
                </label>
                <Input
                  id="ch-edit-target"
                  value={editing.target}
                  onChange={(e) => setEditing((p) => (p ? { ...p, target: e.target.value } : p))}
                  className="mt-1.5"
                />
              </div>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditing(null)}>Cancel</Button>
            <Button
              onClick={handleEditSave}
              disabled={!editing?.name.trim() || !editing?.target.trim()}
            >
              Save Changes
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </Card>
  );
}
