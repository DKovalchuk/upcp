// Agent hooks — TASK-0099 Sprint 2

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  fetchAgents,
  fetchAgent,
  createAgent,
  fetchAgentClaims,
  fetchAgentActivityEvents,
  fetchAgentClarifications,
} from '@/lib/api/agents';
import type { AgentCreate } from '@/types/agent';

export function useAgents(offset = 0, limit = 20) {
  return useQuery({
    queryKey: ['agents', offset, limit],
    queryFn: () => fetchAgents(offset, limit),
  });
}

export function useAgent(agentId: string) {
  return useQuery({
    queryKey: ['agent', agentId],
    queryFn: () => fetchAgent(agentId),
    enabled: !!agentId,
  });
}

export function useCreateAgent() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: AgentCreate) => createAgent(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['agents'] });
    },
  });
}

export function useAgentClaims(agentId: string) {
  return useQuery({
    queryKey: ['agent-claims', agentId],
    queryFn: () => fetchAgentClaims(agentId),
    enabled: !!agentId,
  });
}

export function useAgentActivity(agentId: string) {
  return useQuery({
    queryKey: ['agent-activity', agentId],
    queryFn: () => fetchAgentActivityEvents(agentId),
    enabled: !!agentId,
  });
}

export function useAgentClarifications(agentId: string) {
  return useQuery({
    queryKey: ['agent-clarifications', agentId],
    queryFn: () => fetchAgentClarifications(agentId),
    enabled: !!agentId,
  });
}
