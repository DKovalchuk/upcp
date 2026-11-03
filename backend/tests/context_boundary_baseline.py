"""Documented baseline of existing context-boundary violations — TASK-0177.

Exact ``(file, rule, module) -> (reason, task_ref)`` pairs for the violations
that exist in ``backend/app`` TODAY (inventory 2026-11-02; full narrative in
``tasks/TASK-0177-context-boundary-contract.md``). No globs: a NEW violation
fails ``test_context_boundaries.py``; a fixed one fails as a stale entry, so
TASK-0176 and the rest of the batch must shrink this table when they land.

``task_ref`` legend: ``TASK-xxxx`` = owner task; ``backlog`` = real violation
without an owner (finding); ``—`` = structurally accepted (composition root).
"""

# Exact (file, rule, module) -> (reason, task_ref) for violations existing TODAY (inventory 2026-11-02): no globs, so a new violation fails and a fixed one fails as stale.
BASELINE: dict[tuple[str, str, str], tuple[str, str]] = {
    ("main.py", "foreign-internal", "app.api.registry"): ("composition root wires registry", "—"),
    ("main.py", "foreign-internal", "app.delivery.stale_reaper"): (
        "composition root starts reaper",
        "—",
    ),
    ("main.py", "foreign-internal", "app.identity.middleware"): (
        "composition root adds AuthMiddleware",
        "TASK-0169",
    ),
    ("main.py", "session-local", "SessionLocal"): ("root passes SessionLocal to reaper loop", "—"),
    ("main.py", "redis", "app.shared.redis"): ("root health probe (check_redis_health)", "—"),
    ("api/registry.py", "foreign-internal", "app.identity.agent_endpoints"): (
        "registry assembles context routers",
        "—",
    ),
    ("api/registry.py", "foreign-internal", "app.identity.endpoints"): (
        "registry assembles context routers",
        "—",
    ),
    ("api/registry.py", "foreign-internal", "app.mcp.server"): (
        "registry assembles context routers",
        "—",
    ),
    ("api/v1/agent_self.py", "foreign-model", "app.delivery.models"): (
        "agent-self queries delivery models (audit finding 9)",
        "TASK-0176",
    ),
    ("api/v1/agent_self.py", "foreign-internal", "app.identity.agent_auth"): (
        "consumes agent-auth dep module (not public surface)",
        "backlog",
    ),
    ("api/v1/agent_self.py", "foreign-internal", "app.identity.agents"): (
        "imports Agent/AgentToken carrier module",
        "backlog",
    ),
    ("api/v1/analytics.py", "foreign-internal", "app.reporting.analytics"): (
        "AnalyticsService outside reporting public surface",
        "backlog",
    ),
    ("api/v1/dashboard.py", "foreign-model", "app.projects.models"): (
        "dashboard endpoint queries project model directly",
        "backlog",
    ),
    ("api/v1/dashboard.py", "foreign-internal", "app.reporting.attention"): (
        "attention service outside reporting public surface",
        "backlog",
    ),
    ("api/v1/dashboard.py", "foreign-internal", "app.reporting.dashboard"): (
        "dashboard service outside reporting public surface",
        "backlog",
    ),
    ("api/v1/dashboard.py", "foreign-internal", "app.reporting.portfolio"): (
        "portfolio service outside reporting public surface",
        "backlog",
    ),
    ("api/v1/delivery.py", "foreign-model", "app.delivery.models"): (
        "endpoint types against owner-context models",
        "backlog",
    ),
    ("api/v1/delivery.py", "foreign-internal", "app.delivery.lifecycle"): (
        "endpoint validates transitions via lifecycle",
        "backlog",
    ),
    ("api/v1/notification_channels.py", "foreign-model", "app.reporting.models"): (
        "endpoint queries reporting models directly",
        "backlog",
    ),
    ("api/v1/notification_channels.py", "foreign-internal", "app.reporting.channel_service"): (
        "ChannelService outside public surface",
        "backlog",
    ),
    ("api/v1/notifications.py", "foreign-internal", "app.reporting.sse"): (
        "endpoint consumes SSE manager directly",
        "backlog",
    ),
    ("api/v1/projects.py", "foreign-internal", "app.identity.permissions"): (
        "endpoint consumes RBAC gate (internal module)",
        "backlog",
    ),
    ("api/v1/reaper.py", "foreign-internal", "app.delivery.stale_reaper"): (
        "endpoint drives reaper tick directly",
        "backlog",
    ),
    ("api/v1/reporting.py", "foreign-model", "app.reporting.models"): (
        "endpoint types against owner-context models",
        "backlog",
    ),
    ("api/v1/reporting.py", "foreign-internal", "app.llm.gateway"): (
        "endpoint builds LLM gateway directly",
        "backlog",
    ),
    ("api/v1/reporting.py", "foreign-internal", "app.llm.redaction"): (
        "endpoint builds redactor directly",
        "backlog",
    ),
    ("api/v1/structure.py", "foreign-model", "app.structure.models"): (
        "endpoint types against owner-context models",
        "backlog",
    ),
    ("api/v1/task_workflow.py", "foreign-model", "app.delivery.models"): (
        "endpoint types against owner-context models",
        "backlog",
    ),
    ("api/v1/task_workflow.py", "foreign-internal", "app.delivery.lifecycle"): (
        "endpoint validates transitions via lifecycle",
        "backlog",
    ),
    ("api/v1/task_workflow.py", "foreign-internal", "app.delivery.workflow"): (
        "endpoint drives WorkflowService directly",
        "backlog",
    ),
    ("api/v1/task_workflow.py", "foreign-internal", "app.identity.agent_auth"): (
        "consumes agent-auth dep module (not public surface)",
        "backlog",
    ),
    ("reporting/analytics.py", "foreign-model", "app.delivery.models"): (
        "reporting aggregates via direct model reads",
        "backlog",
    ),
    ("reporting/attention.py", "foreign-model", "app.delivery.models"): (
        "attention dashboard reads delivery models directly",
        "backlog",
    ),
    ("reporting/attention.py", "foreign-model", "app.projects.models"): (
        "attention dashboard reads project models directly",
        "backlog",
    ),
    ("reporting/attention.py", "foreign-model", "app.quality.models"): (
        "attention dashboard reads quality models directly",
        "backlog",
    ),
    ("reporting/dashboard.py", "foreign-model", "app.audit.models"): (
        "dashboard reads audit models directly",
        "backlog",
    ),
    ("reporting/dashboard.py", "foreign-model", "app.delivery.models"): (
        "dashboard reads delivery models directly",
        "backlog",
    ),
    ("reporting/dashboard.py", "foreign-model", "app.projects.models"): (
        "dashboard reads project models directly",
        "backlog",
    ),
    ("reporting/dashboard.py", "foreign-internal", "app.identity.agents"): (
        "dashboard reads identity Agent via agents.py",
        "backlog",
    ),
    ("reporting/portfolio.py", "foreign-model", "app.delivery.models"): (
        "portfolio reads delivery models directly",
        "backlog",
    ),
    ("reporting/portfolio.py", "foreign-model", "app.projects.models"): (
        "portfolio reads project models directly",
        "backlog",
    ),
    ("reporting/service.py", "foreign-model", "app.delivery.models"): (
        "reporting service reads delivery models directly",
        "backlog",
    ),
    ("reporting/service.py", "foreign-model", "app.projects.models"): (
        "reporting service reads project models directly",
        "backlog",
    ),
    ("reporting/trigger.py", "foreign-model", "app.delivery.models"): (
        "trigger reads delivery models directly",
        "backlog",
    ),
    ("mcp/context_pack.py", "session-local", "SessionLocal"): (
        "SessionLocal fallback when caller injects none",
        "TASK-0176",
    ),
    ("mcp/tools.py", "foreign-model", "app.delivery.models"): (
        "mcp tools read delivery models directly",
        "backlog",
    ),
    ("mcp/tools.py", "foreign-internal", "app.delivery.lifecycle"): (
        "mcp tools drive delivery lifecycle directly",
        "backlog",
    ),
    ("mcp/tools.py", "foreign-internal", "app.delivery.workflow"): (
        "mcp tools drive delivery workflow directly",
        "backlog",
    ),
    ("mcp/tools.py", "session-local", "SessionLocal"): (
        "SessionLocal fallback when caller injects none",
        "TASK-0176",
    ),
    ("search/service.py", "foreign-model", "app.delivery.models"): (
        "search aggregates via direct model reads",
        "backlog",
    ),
    ("search/service.py", "foreign-model", "app.projects.models"): (
        "search aggregates via direct model reads",
        "backlog",
    ),
    ("identity/agent_endpoints.py", "foreign-model", "app.delivery.models"): (
        "identity routes query delivery models (audit finding 9)",
        "TASK-0176",
    ),
    ("identity/agent_endpoints.py", "foreign-model", "app.quality.models"): (
        "identity routes query quality models (audit finding 9)",
        "TASK-0176",
    ),
    ("identity/denylist.py", "redis", "app.shared.redis"): (
        "denylist caches inline; auth-path redis -> AuthCacheProvider",
        "TASK-0174",
    ),
    ("identity/middleware.py", "session-local", "SessionLocal"): (
        "middleware queries DB directly; AuthMiddleware retired",
        "TASK-0169",
    ),
    ("identity/middleware.py", "redis", "app.shared.redis"): (
        "subject-state cache inline; -> AuthCacheProvider",
        "TASK-0174",
    ),
    ("identity/permissions.py", "redis", "app.shared.redis"): (
        "permission cache inline; -> AuthCacheProvider",
        "TASK-0175",
    ),
    ("delivery/service.py", "foreign-model", "app.quality.models"): (
        "delivery reads quality DoD models directly",
        "backlog",
    ),
    ("quality/service.py", "foreign-model", "app.delivery.models"): (
        "quality reads delivery models directly",
        "backlog",
    ),
    ("quality/service.py", "foreign-model", "app.projects.models"): (
        "quality reads project models directly",
        "backlog",
    ),
    ("quality/service.py", "foreign-internal", "app.delivery.lifecycle"): (
        "quality validates delivery transitions",
        "backlog",
    ),
    ("shared/event_setup.py", "foreign-internal", "app.reporting.sse"): (
        "shared wires reporting consumers (backward dep)",
        "backlog",
    ),
    ("shared/event_setup.py", "foreign-internal", "app.reporting.trigger"): (
        "shared wires reporting consumers (backward dep)",
        "backlog",
    ),
    ("shared/rate_limit.py", "redis", "app.shared.redis"): (
        "rate-limiter consumes client directly; provider move unowned",
        "TASK-0173",
    ),
}
