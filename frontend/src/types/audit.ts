export interface AuditEvent {
  id: string;
  timestamp: string;
  event_type: string;
  entity_type: string;
  entity_id: string;
  actor_type: string;
  actor_id: string;
  payload: Record<string, unknown> | null;
  note: string | null;
}

export interface AuditEventCreate {
  entity_type: string;
  entity_id: string;
  action: string;
  user_id?: string;
  details?: Record<string, unknown>;
}
