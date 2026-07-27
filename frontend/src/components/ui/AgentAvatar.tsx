import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { AGENT_STATUS_COLORS } from '@/lib/constants';

interface AgentAvatarProps {
  name: string;
  avatarUrl?: string;
  status?: 'working' | 'idle' | 'blocked' | 'offline' | 'stale';
  size?: 'sm' | 'default' | 'lg';
  showPulse?: boolean;
}

const SIZE_CLASSES = {
  sm: 'h-6 w-6',
  default: 'h-8 w-8',
  lg: 'h-10 w-10',
};

const STATUS_DOT_SIZE = {
  sm: 'h-2 w-2 -bottom-0.5 -right-0.5',
  default: 'h-2.5 w-2.5 -bottom-0.5 -right-0.5',
  lg: 'h-3 w-3 -bottom-0.5 -right-0.5',
};

function getInitials(name: string): string {
  return name
    .split(/[\s_-]+/)
    .filter(Boolean)
    .map((w) => w[0])
    .slice(0, 2)
    .join('')
    .toUpperCase();
}

export function AgentAvatar({
  name,
  avatarUrl,
  status,
  size = 'default',
  showPulse = false,
}: AgentAvatarProps) {
  const colors = status ? AGENT_STATUS_COLORS[status] : null;

  return (
    <div className="relative inline-flex shrink-0">
      <Avatar className={SIZE_CLASSES[size]}>
        <AvatarImage src={avatarUrl} alt={name} />
        <AvatarFallback className="bg-violet-500/10 text-violet-600 dark:text-violet-400 text-xs font-medium">
          {getInitials(name)}
        </AvatarFallback>
      </Avatar>
      {status && colors && (
        <span
          className={`absolute ${STATUS_DOT_SIZE[size]} rounded-full border-2 border-background ${colors.dot} ${showPulse ? 'animate-heartbeat-pulse' : ''}`}
        />
      )}
    </div>
  );
}
