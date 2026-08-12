export interface TrendData {
  week: string;
  completed: number;
  created: number;
}

export interface VelocityData {
  week: string;
  count: number;
}

export interface HealthHistoryData {
  date: string;
  completed: number;
  created: number;
  score: number;
}

export interface AgentPerformance {
  agent_id: string;
  total_claims: number;
  completed: number;
  success_rate: number;
  avg_hours: number | null;
}
