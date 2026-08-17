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

// --- Agent Workflow Mock Data ---

export const MOCK_CLAIMS = [
  {
    id: 'claim-1',
    task_id: 'task-2',
    agent_id: 'backend-developer',
    state: 'active',
    claimed_at: new Date(Date.now() - 300000).toISOString(),
    released_at: null,
    last_heartbeat_at: new Date(Date.now() - 60000).toISOString(),
    expires_at: null,
    created_at: new Date(Date.now() - 300000).toISOString(),
  },
];

export const MOCK_CLAIMS_EMPTY: never[] = [];

export const MOCK_HEARTBEATS = [
  {
    id: 'hb-1',
    claim_id: 'claim-1',
    progress_percent: 75,
    current_step: 'Writing unit tests',
    next_step: 'Integration tests',
    blockers: null,
    eta: new Date(Date.now() + 600000).toISOString(),
    created_at: new Date(Date.now() - 60000).toISOString(),
  },
  {
    id: 'hb-2',
    claim_id: 'claim-1',
    progress_percent: 50,
    current_step: 'Implementing JWT generation',
    next_step: 'Unit tests',
    blockers: 'Missing test fixtures',
    eta: null,
    created_at: new Date(Date.now() - 180000).toISOString(),
  },
];

export const MOCK_HEARTBEATS_EMPTY: never[] = [];

export const MOCK_CLARIFICATIONS = [
  {
    id: 'clar-1',
    task_id: 'task-3',
    author_type: 'agent',
    author_id: 'database-architect',
    question: 'Should JWT tokens expire after 15 minutes or 1 hour?',
    context: 'Implementing token expiry configuration',
    blocking: true,
    state: 'open',
    answer: null,
    answered_by: null,
    answered_at: null,
    created_at: new Date(Date.now() - 300000).toISOString(),
  },
];

export const MOCK_CLARIFICATIONS_EMPTY: never[] = [];

export const MOCK_EVIDENCE = [
  {
    id: 'ev-1',
    task_id: 'task-1',
    dod_item_id: null,
    type: 'test_output',
    title: 'Unit test results',
    description: 'All 42 tests passing',
    url: null,
    content_snippet: '42 passed, 0 failed',
    artifact_ref: null,
    created_by_type: 'agent',
    created_by_id: 'qa-engineer',
    verification_state: 'unverified',
    verified_by_type: null,
    verified_by_id: null,
    verified_at: null,
    created_at: new Date(Date.now() - 120000).toISOString(),
    updated_at: new Date(Date.now() - 120000).toISOString(),
  },
  {
    id: 'ev-2',
    task_id: 'task-1',
    dod_item_id: null,
    type: 'diff',
    title: 'Git diff of changes',
    description: 'Changes to auth service',
    url: 'https://github.com/upcp/core/pull/42',
    content_snippet: null,
    artifact_ref: null,
    created_by_type: 'agent',
    created_by_id: 'backend-developer',
    verification_state: 'agent_verified',
    verified_by_type: 'agent',
    verified_by_id: 'backend-developer',
    verified_at: new Date(Date.now() - 60000).toISOString(),
    created_at: new Date(Date.now() - 180000).toISOString(),
    updated_at: new Date(Date.now() - 60000).toISOString(),
  },
];

export const MOCK_EVIDENCE_ACCEPTED = [
  {
    ...MOCK_EVIDENCE[0],
    id: 'ev-3',
    verification_state: 'human_accepted',
    verified_by_type: 'human',
    verified_by_id: 'user-1',
    verified_at: new Date(Date.now() - 30000).toISOString(),
  },
];

export const MOCK_EVIDENCE_REJECTED = [
  {
    ...MOCK_EVIDENCE[0],
    id: 'ev-4',
    verification_state: 'rejected',
    verified_by_type: 'human',
    verified_by_id: 'user-1',
    verified_at: new Date(Date.now() - 30000).toISOString(),
  },
];

export const MOCK_EVIDENCE_EMPTY: never[] = [];

export const MOCK_REVIEW_ROUNDS = [
  {
    id: 'rr-1',
    task_id: 'task-1',
    requested_by_type: 'agent',
    requested_by_id: 'backend-developer',
    reviewer_type: 'agent',
    reviewer_id: 'code-quality-guard',
    state: 'completed',
    verdict: 'approve',
    confidence: 92,
    summary: 'Code quality excellent, all tests pass',
    created_at: new Date(Date.now() - 600000).toISOString(),
    started_at: new Date(Date.now() - 550000).toISOString(),
    completed_at: new Date(Date.now() - 300000).toISOString(),
  },
];

export const MOCK_REVIEW_ROUNDS_PENDING = [
  {
    id: 'rr-2',
    task_id: 'task-2',
    requested_by_type: 'agent',
    requested_by_id: 'backend-developer',
    reviewer_type: 'agent',
    reviewer_id: 'code-quality-guard',
    state: 'in_progress',
    verdict: null,
    confidence: null,
    summary: null,
    created_at: new Date(Date.now() - 120000).toISOString(),
    started_at: new Date(Date.now() - 100000).toISOString(),
    completed_at: null,
  },
];

export const MOCK_REVIEW_FINDINGS = [
  {
    id: 'rf-1',
    review_round_id: 'rr-1',
    severity: 'minor',
    category: 'style',
    message: 'Consider using a more descriptive variable name',
    evidence_id: null,
    dod_item_id: null,
    suggestion: 'Rename `tmp` to `tempToken`',
    created_at: new Date(Date.now() - 400000).toISOString(),
  },
];

export const MOCK_REVIEW_ROUNDS_EMPTY: never[] = [];

// --- Dashboard Agent Activity ---

export const MOCK_AGENT_ACTIVITY = [
  {
    agent_id: 'backend-developer',
    agent_name: 'Backend Developer',
    task_id: 'task-2',
    task_title: 'Implement auth middleware',
    claimed_at: new Date(Date.now() - 600000).toISOString(),
    last_heartbeat_at: new Date(Date.now() - 60000).toISOString(),
    progress_percent: 65,
    current_step: 'Writing middleware',
    is_stale: false,
  },
];

export const MOCK_AGENT_ACTIVITY_STALE = [
  {
    agent_id: 'database-architect',
    agent_name: 'Database Architect',
    task_id: 'task-3',
    task_title: 'Add RBAC models',
    claimed_at: new Date(Date.now() - 1800000).toISOString(),
    last_heartbeat_at: new Date(Date.now() - 600000).toISOString(),
    progress_percent: 30,
    current_step: 'Schema design',
    is_stale: true,
  },
];

export const MOCK_AGENT_ACTIVITY_EMPTY: never[] = [];

// --- Attention Dashboard ---

export const MOCK_ATTENTION = {
  needs_review: [
    { task_id: 'task-4', task_title: 'Write auth unit tests', count: 1 },
  ],
  open_questions: [
    { task_id: 'task-3', task_title: 'Add RBAC models', count: 1 },
  ],
  blocked_tasks: [
    { task_id: 'task-3', task_title: 'Add RBAC models' },
  ],
  stale_claims: [],
  failed_dod: [],
  rejected_tasks: [],
  agent_verdicts_waiting: [],
  low_health_projects: [],
  recent_activity: MOCK_AUDIT_EVENTS.slice(0, 3),
};

export const MOCK_NOTIFICATIONS = [
  {
    id: 'notif-1',
    user_id: 'user-1',
    type: 'agent.claimed',
    title: 'Task claimed',
    message: 'Backend Developer claimed "Implement auth middleware"',
    entity_type: 'task',
    entity_id: 'task-2',
    is_read: false,
    created_at: new Date(Date.now() - 600000).toISOString(),
  },
  {
    id: 'notif-2',
    user_id: 'user-1',
    type: 'clarification.open',
    title: 'Clarification requested',
    message: 'Database Architect asked about JWT token expiry',
    entity_type: 'task',
    entity_id: 'task-3',
    is_read: false,
    created_at: new Date(Date.now() - 300000).toISOString(),
  },
];

export const MOCK_NOTIFICATIONS_EMPTY: never[] = [];
