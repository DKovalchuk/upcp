export interface AuditEvent {
  id: string;
  entity_type: string;
  entity_id: string;
  action: string;
  user_id: string | null;
  details: Record<string, unknown> | null;
  created_at: string;
}

export interface AuditEventCreate {
  entity_type: string;
  entity_id: string;
  action: string;
  user_id?: string;
  details?: Record<string, unknown>;
}
