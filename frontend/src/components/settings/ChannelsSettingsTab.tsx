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
import { Radio, Plus, Trash2, ExternalLink } from 'lucide-react';
import { showToast } from '@/lib/toast';
import { useNotificationChannels } from '@/hooks/use-analytics';
import {
  createNotificationChannel,
  deleteNotificationChannel,
  toggleNotificationChannel,
  testNotificationChannel,
} from '@/lib/api/analytics';

export function ChannelsSettingsTab() {
  const queryClient = useQueryClient();
  const { data, isLoading } = useNotificationChannels();
  const channels = data?.items ?? [];
  const [showCreate, setShowCreate] = useState(false);
  const [newChannel, setNewChannel] = useState<{
    channel_type: string;
    name: string;
    target: string;
  }>({ channel_type: 'email', name: '', target: '' });

  const handleCreate = async () => {
    if (!newChannel.name.trim() || !newChannel.target.trim()) return;
    const config = newChannel.channel_type === 'email'
      ? { smtp_host: 'smtp.example.com', smtp_port: 587, from_address: 'noreply@example.com', to_address: newChannel.target }
      : { url: newChannel.target };
    try {
      await createNotificationChannel({ channel_type: newChannel.channel_type, name: newChannel.name, config });
      queryClient.invalidateQueries({ queryKey: ['notification-channels'] });
      setNewChannel({ channel_type: 'email', name: '', target: '' });
      setShowCreate(false);
      showToast.created('Channel');
    } catch {
      showToast.mutationError('create', 'channel');
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await deleteNotificationChannel(id);
      queryClient.invalidateQueries({ queryKey: ['notification-channels'] });
      showToast.deleted('Channel');
    } catch {
      showToast.mutationError('delete', 'channel');
    }
  };

  const handleToggle = async (id: string) => {
    try {
      await toggleNotificationChannel(id);
      queryClient.invalidateQueries({ queryKey: ['notification-channels'] });
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
    </Card>
  );
}
