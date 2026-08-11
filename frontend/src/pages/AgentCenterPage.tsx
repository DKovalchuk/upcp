// Agent Center page — TASK-0099 Sprint 2

import { useState } from 'react';
import { useNavigate } from '@tanstack/react-router';
import { useAgents, useCreateAgent } from '@/hooks/use-agents';
import { AgentCard } from '@/components/agents/AgentCard';
import { AgentTable } from '@/components/agents/AgentTable';
import { AgentToolbar } from '@/components/agents/AgentToolbar';
import { Button } from '@/components/ui/button';
import { EmptyState } from '@/components/ui/EmptyState';
import { PageSkeleton } from '@/components/ui/PageSkeleton';
import { EntityFormDialog } from '@/components/forms/EntityFormDialog';
import { Plus, Bot } from 'lucide-react';
import { showToast } from '@/lib/toast';

const agentFields = [
  { name: 'name', label: 'Name', type: 'text' as const, required: true },
  { name: 'description', label: 'Description', type: 'textarea' as const },
];

export function AgentCenterPage() {
  const [viewMode, setViewMode] = useState<'grid' | 'table'>('grid');
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [showCreate, setShowCreate] = useState(false);
  const navigate = useNavigate();

  const { data, isLoading } = useAgents(0, 100);
  const createAgent = useCreateAgent();

  const agents = data?.items ?? [];

  const filtered = agents.filter((a) => {
    if (search && !a.name.toLowerCase().includes(search.toLowerCase())) return false;
    return true;
  });

  if (isLoading) {
    return <PageSkeleton hasHeader hasCards cardCount={6} />;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Agents</h1>
          <p className="text-muted-foreground">
            Manage AI agents, tokens, and assignments
          </p>
        </div>
        <Button onClick={() => setShowCreate(true)}>
          <Plus className="mr-2 h-4 w-4" />
          New Agent
        </Button>
      </div>

      <AgentToolbar
        search={search}
        onSearchChange={setSearch}
        statusFilter={statusFilter}
        onStatusFilterChange={setStatusFilter}
        viewMode={viewMode}
        onViewModeChange={setViewMode}
      />

      {filtered.length === 0 ? (
        <EmptyState
          icon={Bot}
          title="No agents"
          description="Create your first AI agent to get started"
          action={{ label: 'New Agent', onClick: () => setShowCreate(true) }}
        />
      ) : viewMode === 'grid' ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {filtered.map((agent) => (
            <AgentCard
              key={agent.id}
              agent={agent}
              onSelect={() =>
                navigate({ to: '/agents/$agentId', params: { agentId: agent.id } })
              }
            />
          ))}
        </div>
      ) : (
        <AgentTable
          agents={filtered}
          onSelect={(id) =>
            navigate({ to: '/agents/$agentId', params: { agentId: id } })
          }
        />
      )}

      <EntityFormDialog
        open={showCreate}
        onOpenChange={setShowCreate}
        title="Create Agent"
        fields={agentFields}
        onSubmit={async (data) => {
          await createAgent.mutateAsync(data as { name: string; description?: string });
          showToast.created('Agent');
          setShowCreate(false);
        }}
      />
    </div>
  );
}
