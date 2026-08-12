import { useState } from 'react';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { ProfileTab } from '@/components/settings/ProfileTab';
import { NotificationsTab } from '@/components/settings/NotificationsTab';
import { ChannelsSettingsTab } from '@/components/settings/ChannelsSettingsTab';
import { AppearanceTab } from '@/components/settings/AppearanceTab';
import { AboutTab } from '@/components/settings/AboutTab';
import { Settings, User, Bell, Radio, Palette, Info } from 'lucide-react';

const TABS = [
  { value: 'profile', label: 'Profile', icon: User },
  { value: 'notifications', label: 'Notifications', icon: Bell },
  { value: 'channels', label: 'Channels', icon: Radio },
  { value: 'appearance', label: 'Appearance', icon: Palette },
  { value: 'about', label: 'About', icon: Info },
] as const;

export function SettingsPage() {
  const [activeTab, setActiveTab] = useState('profile');

  return (
    <div className="space-y-[clamp(2rem,4vw,3rem)]">
      <div className="flex items-center gap-2">
        <Settings className="h-5 w-5" />
        <h1 className="text-2xl font-bold tracking-tight">Settings</h1>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList variant="line" aria-label="Settings sections">
          {TABS.map((tab) => (
            <TabsTrigger
              key={tab.value}
              value={tab.value}
              aria-controls={`settings-panel-${tab.value}`}
            >
              <tab.icon className="h-4 w-4" aria-hidden="true" />
              <span className="hidden sm:inline">{tab.label}</span>
            </TabsTrigger>
          ))}
        </TabsList>

        <TabsContent value="profile" id="settings-panel-profile" role="tabpanel" aria-label="Profile settings">
          <ProfileTab />
        </TabsContent>
        <TabsContent value="notifications" id="settings-panel-notifications" role="tabpanel" aria-label="Notification settings">
          <NotificationsTab />
        </TabsContent>
        <TabsContent value="channels" id="settings-panel-channels" role="tabpanel" aria-label="Channel settings">
          <ChannelsSettingsTab />
        </TabsContent>
        <TabsContent value="appearance" id="settings-panel-appearance" role="tabpanel" aria-label="Appearance settings">
          <AppearanceTab />
        </TabsContent>
        <TabsContent value="about" id="settings-panel-about" role="tabpanel" aria-label="About">
          <AboutTab />
        </TabsContent>
      </Tabs>
    </div>
  );
}
