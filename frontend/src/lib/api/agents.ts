// Agent API functions — TASK-0099 Sprint 2

import type {
  AgentWithMetrics,
  AgentListResponse,
  AgentCreate,
  AgentUpdate,
  AgentClaim,
  AgentActivityEvent,
  AgentClarification,
} from '@/types/agent';
import { apiRequest, paginationParams } from './client';

// ── Agent CRUD ──

export async function fetchAgents(
  offset = 0,
  limit = 20
): Promise<AgentListResponse> {
  return apiRequest<AgentListResponse>(
    `/api/v1/agents?${paginationParams({ offset, limit })}`
  );
}

export async function fetchAgent(agentId: string): Promise<AgentWithMetrics> {
  return apiRequest<AgentWithMetrics>(`/api/v1/agents/${agentId}`);
}

export async function createAgent(data: AgentCreate): Promise<AgentWithMetrics> {
  return apiRequest<AgentWithMetrics>('/api/v1/agents', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function updateAgent(
  agentId: string,
  data: AgentUpdate
): Promise<AgentWithMetrics> {
  return apiRequest<AgentWithMetrics>(`/api/v1/agents/${agentId}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
}

// ── Agent Detail Endpoints ──

export async function fetchAgentClaims(
  agentId: string
): Promise<{ items: AgentClaim[] }> {
  return apiRequest<{ items: AgentClaim[] }>(
    `/api/v1/agents/${agentId}/claims`
  );
}

export async function fetchAgentActivityEvents(
  agentId: string
): Promise<{ items: AgentActivityEvent[] }> {
  return apiRequest<{ items: AgentActivityEvent[] }>(
    `/api/v1/agents/${agentId}/activity`
  );
}

export async function fetchAgentClarifications(
  agentId: string
): Promise<{ items: AgentClarification[] }> {
  return apiRequest<{ items: AgentClarification[] }>(
    `/api/v1/agents/${agentId}/clarifications`
  );
}
