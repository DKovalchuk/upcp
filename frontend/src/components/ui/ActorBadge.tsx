import { Badge } from '@/components/ui/badge';
import { ACTOR_COLORS } from '@/lib/constants';
import { Bot, User, Cpu } from 'lucide-react';

interface ActorBadgeProps {
  actorType: 'agent' | 'human' | 'system';
  actorName?: string;
}

const ICONS = {
  agent: Bot,
  human: User,
  system: Cpu,
};

export function ActorBadge({ actorType, actorName }: ActorBadgeProps) {
  const colors = ACTOR_COLORS[actorType];
  const Icon = ICONS[actorType];

  return (
    <Badge
      variant="outline"
      className={`${colors.bg} ${colors.text} ${colors.border} gap-1.5`}
    >
      <Icon className="h-3 w-3" />
      {actorName || actorType}
    </Badge>
  );
}
