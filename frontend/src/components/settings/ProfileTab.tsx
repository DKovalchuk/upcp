import { useState, useCallback } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { authPasswordChange } from '@/lib/auth';
import { showToast } from '@/lib/toast';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { User, Shield, Save } from 'lucide-react';

export function ProfileTab() {
  const { user, token } = useAuth();
  const [currentPw, setCurrentPw] = useState('');
  const [newPw, setNewPw] = useState('');
  const [confirmPw, setConfirmPw] = useState('');
  const [saving, setSaving] = useState(false);

  const handleChangePassword = useCallback(async () => {
    if (!token) return;
    if (newPw !== confirmPw) {
      showToast.error('Passwords do not match');
      return;
    }
    if (newPw.length < 8) {
      showToast.error('Password must be at least 8 characters');
      return;
    }
    setSaving(true);
    try {
      await authPasswordChange(token, currentPw, newPw);
      showToast.success('Password changed successfully');
      setCurrentPw('');
      setNewPw('');
      setConfirmPw('');
    } catch (err: any) {
      showToast.error(err?.message ?? 'Failed to change password');
    } finally {
      setSaving(false);
    }
  }, [token, currentPw, newPw, confirmPw]);

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader className="flex flex-row items-center gap-2 space-y-0 pb-2">
          <User className="h-4 w-4" />
          <CardTitle>Profile</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div>
              <p className="text-sm font-medium">Name</p>
              <p className="text-sm text-muted-foreground">{user?.display_name ?? '—'}</p>
            </div>
            <div>
              <p className="text-sm font-medium">Email</p>
              <p className="text-sm text-muted-foreground">{user?.email ?? '—'}</p>
            </div>
            {user?.is_superuser && (
              <span className="inline-block rounded bg-primary/10 px-2 py-0.5 text-xs font-medium text-primary">
                Admin
              </span>
            )}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center gap-2 space-y-0 pb-2">
          <Shield className="h-4 w-4" />
          <CardTitle>Change Password</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div>
              <label className="text-xs font-medium text-muted-foreground">Current password</label>
              <Input
                type="password"
                value={currentPw}
                onChange={(e) => setCurrentPw(e.target.value)}
                placeholder="••••••••"
              />
            </div>
            <div>
              <label className="text-xs font-medium text-muted-foreground">New password</label>
              <Input
                type="password"
                value={newPw}
                onChange={(e) => setNewPw(e.target.value)}
                placeholder="••••••••"
              />
            </div>
            <div>
              <label className="text-xs font-medium text-muted-foreground">Confirm new password</label>
              <Input
                type="password"
                value={confirmPw}
                onChange={(e) => setConfirmPw(e.target.value)}
                placeholder="••••••••"
              />
            </div>
            <Button
              size="sm"
              onClick={handleChangePassword}
              disabled={saving || !currentPw || !newPw || !confirmPw}
            >
              <Save className="mr-1 h-3 w-3" />
              {saving ? 'Saving...' : 'Change Password'}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
