// Agent Table component — TASK-0099 Sprint 2

import { AgentAvatar } from '@/components/ui/AgentAvatar';
import { AgentStatusBadge } from '@/components/ui/AgentStatusBadge';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { formatRelativeTime } from '@/lib/format';
import type { AgentProfile } from '@/types/agent';

interface AgentTableProps {
  agents: AgentProfile[];
  onSelect: (id: string) => void;
}

export function AgentTable({ agents, onSelect }: AgentTableProps) {
  return (
    <div className="rounded-md border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Agent</TableHead>
            <TableHead>Status</TableHead>
            <TableHead>Created</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {agents.map((agent) => (
            <TableRow
              key={agent.id}
              className="cursor-pointer"
              onClick={() => onSelect(agent.id)}
            >
              <TableCell>
                <div className="flex items-center gap-2">
                  <AgentAvatar name={agent.name} size="sm" />
                  <span className="font-medium">{agent.name}</span>
                </div>
              </TableCell>
              <TableCell>
                <AgentStatusBadge
                  status={agent.is_active ? 'idle' : 'offline'}
                />
              </TableCell>
              <TableCell className="text-muted-foreground">
                {formatRelativeTime(agent.created_at)}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
