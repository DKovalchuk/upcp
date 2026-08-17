// Agent Claims Tab — TASK-0099 Sprint 2

import { useAgentClaims } from '@/hooks/use-agents';
import { EmptyState } from '@/components/ui/EmptyState';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { formatRelativeTime } from '@/lib/format';
import { ClipboardList } from 'lucide-react';

interface AgentClaimsTabProps {
  agentId: string;
}

export function AgentClaimsTab({ agentId }: AgentClaimsTabProps) {
  const { data, isLoading } = useAgentClaims(agentId);
  const claims = data?.items ?? [];

  if (isLoading) {
    return <div className="text-sm text-muted-foreground">Loading...</div>;
  }

  if (claims.length === 0) {
    return (
      <EmptyState
        icon={ClipboardList}
        title="No claims"
        description="This agent has not claimed any tasks yet"
      />
    );
  }

  return (
    <div className="rounded-md border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Task</TableHead>
            <TableHead>Status</TableHead>
            <TableHead>Claimed</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {claims.map((claim) => (
            <TableRow key={claim.id}>
              <TableCell className="font-medium">
                {claim.task_title ?? claim.task_id}
              </TableCell>
              <TableCell>
                <StatusBadge status={claim.state} />
              </TableCell>
              <TableCell className="text-muted-foreground">
                {claim.claimed_at ? formatRelativeTime(claim.claimed_at) : '—'}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
