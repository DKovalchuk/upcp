export const MOCK_USER = {
  id: 'user-1',
  email: 'admin@upcp.dev',
  display_name: 'Admin',
  is_active: true,
  is_superuser: true,
  organizations: [{ id: 'org-1', name: 'Default', role: 'admin' }],
};

export const MOCK_TOKENS = {
  access_token: 'mock-access-token',
  refresh_token: 'mock-refresh-token',
  token_type: 'bearer',
};

export const MOCK_PROJECTS = [
  {
    id: 'proj-1',
    name: 'UPCP Core',
    slug: 'upcp-core',
    description: 'Universal Project Control Plane core platform',
    status: 'active',
    created_at: '2026-01-15T10:00:00Z',
    updated_at: '2026-07-24T14:30:00Z',
  },
  {
    id: 'proj-2',
    name: 'Mobile App',
    slug: 'mobile-app',
    description: 'iOS/Android companion app',
    status: 'active',
    created_at: '2026-03-01T08:00:00Z',
    updated_at: '2026-07-20T09:15:00Z',
  },
];

export const MOCK_DASHBOARD_STATS = {
  project_count: 2,
  task_counts_by_status: {
    backlog: 5,
    in_progress: 3,
    review: 2,
    done: 12,
  },
  recent_projects: MOCK_PROJECTS,
  recent_activity: [
    {
      id: 'evt-1',
      timestamp: new Date(Date.now() - 5 * 60000).toISOString(),
      event_type: 'completed',
      entity_type: 'task',
      entity_id: 'task-1',
      actor_type: 'agent',
      actor_id: 'code-quality-guard',
      payload: null,
      note: null,
    },
    {
      id: 'evt-2',
      timestamp: new Date(Date.now() - 15 * 60000).toISOString(),
      event_type: 'claimed',
      entity_type: 'task',
      entity_id: 'task-2',
      actor_type: 'agent',
      actor_id: 'backend-developer',
      payload: null,
      note: null,
    },
  ],
};

export const MOCK_FEATURES = [
  {
    id: 'feat-1',
    project_id: 'proj-1',
    name: 'Authentication',
    slug: 'auth',
    description: 'User authentication and authorization',
    status: 'in-progress',
    created_at: '2026-01-20T10:00:00Z',
    updated_at: '2026-07-24T14:00:00Z',
  },
  {
    id: 'feat-2',
    project_id: 'proj-1',
    name: 'Agent Workflow',
    slug: 'agent-workflow',
    description: 'AI agent workflow management',
    status: 'backlog',
    created_at: '2026-02-01T10:00:00Z',
    updated_at: '2026-07-20T10:00:00Z',
  },
];

export const MOCK_TASKS = [
  {
    id: 'task-1',
    feature_id: 'feat-1',
    title: 'Implement JWT token service',
    description: 'Create JWT token generation and validation service',
    status: 'done',
    priority: 0,
    assignee_type: 'agent',
    assignee_id: 'backend-developer',
    component_id: 'comp-1',
    module_id: null,
    created_at: '2026-01-25T10:00:00Z',
    updated_at: '2026-07-22T16:00:00Z',
  },
  {
    id: 'task-2',
    feature_id: 'feat-1',
    title: 'Implement auth middleware',
    description: 'Create authentication middleware for all API routes',
    status: 'in-progress',
    priority: 1,
    assignee_type: 'agent',
    assignee_id: 'code-quality-guard',
    component_id: 'comp-1',
    module_id: null,
    created_at: '2026-02-01T10:00:00Z',
    updated_at: new Date(Date.now() - 30 * 60000).toISOString(),
  },
  {
    id: 'task-3',
    feature_id: 'feat-1',
    title: 'Add RBAC models',
    description: 'Role-based access control data models',
    status: 'blocked',
    priority: 0,
    assignee_type: 'agent',
    assignee_id: 'database-architect',
    component_id: 'comp-1',
    module_id: null,
    created_at: '2026-02-10T10:00:00Z',
    updated_at: new Date(Date.now() - 120 * 60000).toISOString(),
  },
  {
    id: 'task-4',
    feature_id: 'feat-1',
    title: 'Write auth unit tests',
    description: 'Comprehensive unit tests for auth service',
    status: 'ready_for_review',
    priority: 2,
    assignee_type: 'agent',
    assignee_id: 'qa-engineer',
    component_id: 'comp-1',
    module_id: null,
    created_at: '2026-02-15T10:00:00Z',
    updated_at: new Date(Date.now() - 60 * 60000).toISOString(),
  },
];

export const MOCK_COMPONENTS = [
  {
    id: 'comp-1',
    project_id: 'proj-1',
    name: 'Backend API',
    slug: 'backend-api',
    description: 'Python FastAPI backend',
    created_at: '2026-01-15T10:00:00Z',
    updated_at: '2026-07-24T14:00:00Z',
  },
];

export const MOCK_HEALTH = {
  status: 'healthy',
  service: 'upcp-api',
};

export const MOCK_QUALITY_STATS = {
  total_tasks: 22,
  tasks_with_ac: 15,
  total_ac: 45,
  passed_ac: 38,
  total_dod: 30,
  passed_dod: 25,
  pass_rate: 0.84,
};

export const MOCK_AUDIT_EVENTS = [
  {
    id: 'audit-1',
    timestamp: new Date(Date.now() - 5 * 60000).toISOString(),
    event_type: 'completed',
    entity_type: 'task',
    entity_id: 'task-1',
    actor_type: 'agent',
    actor_id: 'code-quality-guard',
    payload: { status: 'done' },
    note: 'All acceptance criteria met',
  },
  {
    id: 'audit-2',
    timestamp: new Date(Date.now() - 30 * 60000).toISOString(),
    event_type: 'claimed',
    entity_type: 'task',
    entity_id: 'task-2',
    actor_type: 'agent',
    actor_id: 'backend-developer',
    payload: null,
    note: null,
  },
  {
    id: 'audit-3',
    timestamp: new Date(Date.now() - 60 * 60000).toISOString(),
    event_type: 'approved',
    entity_type: 'task',
    entity_id: 'task-1',
    actor_type: 'human',
    actor_id: 'user-1',
    payload: null,
    note: 'Approved after review',
  },
];
