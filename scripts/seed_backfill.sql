-- TASK-0166 — dev seed: SQL backfill for domains without a write API.
-- Run after scripts/seed_full.py + scripts/seed_mechanisms.py:
--   docker exec -i upcp-dev-db-1 psql -U upcp -d upcp -v ON_ERROR_STOP=1 \
--     < scripts/seed_backfill.sql
--
-- Covers: membership, audit_event (Recent Activity + project audit pages),
-- git branches/commits, task dependencies, analytics history backdating,
-- stale claim heartbeat (attention section).

\set ON_ERROR_STOP on

-- ── 1. Membership: admin owns the default org (/auth/me organizations) ──
INSERT INTO membership (id, user_id, org_id, role, created_at)
SELECT gen_random_uuid()::text, u.id, o.id, 'owner', now()
FROM user_account u
JOIN organization o ON o.is_default = true
WHERE u.email = 'admin@dev.com'
ON CONFLICT (user_id, org_id) DO NOTHING;
SELECT 'membership' AS entity, count(*) FROM membership;

-- ── 2. Audit events: dashboard Recent Activity feed reads ALL rows (endpoint
--       caps at 10); the project audit page filters entity_id = project_id,
--       so UPCP gets an extra batch for a full page. ────────────────────────
WITH proj AS (SELECT id, slug FROM project),
     ev(event_type, actor, entity_name, status, hours_ago, note) AS (
       VALUES
         ('project_created',   'human',  'project', 'active',    220, 'Project bootstrapped from seed'),
         ('task_completed',    'agent',  'task',    'done',      180, 'Batch of tasks closed by agent run'),
         ('quality_gate_passed','system','quality', 'passed',    120, 'quality:gate exited 0'),
         ('review_completed',  'agent',  'review',  'approve',    72, 'Agent verdict approved with 92% confidence'),
         ('task_status_changed','human', 'task',    'in_progress', 9, 'Board drag-move recorded')
     )
INSERT INTO audit_event (id, timestamp, event_type, entity_type, entity_id,
                         actor_type, actor_id, payload, note)
SELECT gen_random_uuid()::text,
       now() - (ev.hours_ago || ' hours')::interval,
       ev.event_type,
       'project',
       p.id,
       ev.actor,
       COALESCE((SELECT id FROM user_account WHERE email = 'admin@dev.com')::text, 'system'),
       jsonb_build_object('actor_name', CASE ev.actor WHEN 'agent' THEN 'qa-engineer'
                                                       WHEN 'system' THEN 'quality-gate'
                                                       ELSE 'Admin' END,
                          'entity_name', p.slug,
                          'status', ev.status),
       ev.note
FROM proj p CROSS JOIN ev
WHERE NOT EXISTS (SELECT 1 FROM audit_event ae
                  WHERE ae.entity_id = p.id AND ae.note = ev.note);

-- UPCP gets a second batch (project audit page = 15 rows)
WITH up AS (SELECT id, slug FROM project WHERE slug = 'upcp'),
     ev(event_type, actor, status, hours_ago, note) AS (
       VALUES
         ('evidence_attached',  'agent',  'accepted',    60, 'Evidence human-accepted after agent verify'),
         ('clarification_answered','agent','answered',    48, 'Blocking clarification answered'),
         ('task_claimed',       'agent',  'active',      36, 'Agent claimed a ready task'),
         ('claim_released',     'system', 'released',    30, 'Reaper released a dead claim'),
         ('review_rejected',    'agent',  'reject',      24, 'Review rejected with 80% confidence'),
         ('task_completed',     'human',  'done',        18, 'Task closed after gate passed'),
         ('feature_created',    'human',  'in_progress', 15, 'Feature added to backlog'),
         ('quality_gate_passed','system', 'passed',      12, 'Nightly quality gate exited 0'),
         ('agent_stale',        'system', 'stale',        6, 'Stale claim detected by reaper'),
         ('task_status_changed','human',  'ready_for_review', 3, 'Submitted for review from the board')
     )
INSERT INTO audit_event (id, timestamp, event_type, entity_type, entity_id,
                         actor_type, actor_id, payload, note)
SELECT gen_random_uuid()::text,
       now() - (ev.hours_ago || ' hours')::interval,
       ev.event_type,
       'project',
       up.id,
       ev.actor,
       COALESCE((SELECT id FROM user_account WHERE email = 'admin@dev.com')::text, 'system'),
       jsonb_build_object('actor_name', CASE ev.actor WHEN 'agent' THEN 'qa-engineer'
                                                       WHEN 'system' THEN 'reaper'
                                                       ELSE 'Admin' END,
                          'entity_name', up.slug,
                          'status', ev.status),
       ev.note
FROM up CROSS JOIN ev
WHERE NOT EXISTS (SELECT 1 FROM audit_event ae
                  WHERE ae.entity_id = up.id AND ae.note = ev.note);
SELECT 'audit_event' AS entity, count(*) FROM audit_event;

-- ── 3. Git branches + commits for the seeded provider ─────────────────────
INSERT INTO git_branch (id, provider_id, name, last_commit_sha, is_default, created_at)
SELECT gen_random_uuid()::text, gp.id, b.name, b.sha, b.is_def, now()
FROM git_provider gp
CROSS JOIN (VALUES
  ('develop',         '9f3c1a2b7d4e5f608192a3b4c5d6e7f801234abc', true),
  ('main',            '1a2b3c4d5e6f708192a3b4c5d6e7f801234abcd0', false),
  ('release/0.22.0',  '2b3c4d5e6f708192a3b4c5d6e7f801234abcd0ef', false)
) AS b(name, sha, is_def)
WHERE gp.url LIKE '%upcp%'
  AND NOT EXISTS (SELECT 1 FROM git_branch gb WHERE gb.provider_id = gp.id);

INSERT INTO git_commit (id, provider_id, sha, message, author, committed_at, created_at)
SELECT gen_random_uuid()::text, gp.id, c.sha, c.message, c.author,
       now() - (c.hours || ' hours')::interval, now()
FROM git_provider gp
CROSS JOIN (VALUES
  ('9f3c1a2b7d4e5f608192a3b4c5d6e7f801234abc', 'fix(quality): verdict endpoint typing (TASK-0160)', 'Dmitry',  9),
  ('1a2b3c4d5e6f708192a3b4c5d6e7f801234abcd0', 'feat(dashboard): attention card-scoped locators (TASK-0165)', 'Dmitry', 30),
  ('2b3c4d5e6f708192a3b4c5d6e7f801234abcd0ef', 'chore: bump version to 0.22.0', 'Dmitry', 72),
  ('3c4d5e6f708192a3b4c5d6e7f801234abcd0ef1a', 'fix(identity): unique jti in access tokens (TASK-0159)', 'Dmitry', 96),
  ('4d5e6f708192a3b4c5d6e7f801234abcd0ef1a2b', 'test(hermetic): drop-before-create in local _db fixtures', 'Dmitry', 100),
  ('5e6f708192a3b4c5d6e7f801234abcd0ef1a2b3c', 'docs(TASK-0160): doc/status sync evidence', 'Dmitry', 110)
) AS c(sha, message, author, hours)
WHERE gp.url LIKE '%upcp%'
  AND NOT EXISTS (SELECT 1 FROM git_commit gc WHERE gc.sha = c.sha);
SELECT 'git_branch' AS entity, count(*) FROM git_branch
UNION ALL SELECT 'git_commit', count(*) FROM git_commit;

-- ── 4. Task dependencies (no HTTP endpoint exists) — acyclic pairs ────────
INSERT INTO task_dependency (id, task_id, blocked_by_task_id, created_at)
SELECT gen_random_uuid()::text, a.id, b.id, now()
FROM task a, task b
WHERE a.title = 'Branch listing and commit history'
  AND b.title = 'Git provider CRUD (GitLab, GitHub)'
  AND NOT EXISTS (SELECT 1 FROM task_dependency d
                  WHERE d.task_id = a.id AND d.blocked_by_task_id = b.id);
INSERT INTO task_dependency (id, task_id, blocked_by_task_id, created_at)
SELECT gen_random_uuid()::text, a.id, b.id, now()
FROM task a, task b
WHERE a.title = 'Task-to-commit linking'
  AND b.title = 'Branch listing and commit history'
  AND NOT EXISTS (SELECT 1 FROM task_dependency d
                  WHERE d.task_id = a.id AND d.blocked_by_task_id = b.id);
SELECT 'task_dependency' AS entity, count(*) FROM task_dependency;

-- ── 5. Analytics history: spread UPCP done-tasks across the last 8 weeks
--       (velocity / trends / health-history read created_at + updated_at).
--       The most recent batch stays inside 7 days for done_this_week KPI. ──
WITH ranked AS (
  SELECT id, row_number() OVER (ORDER BY created_at) AS rn
  FROM task
  WHERE status = 'done'
    AND feature_id IN (SELECT id FROM feature
                       WHERE project_id = (SELECT id FROM project WHERE slug = 'upcp'))
),
total AS (SELECT count(*) AS n FROM ranked)
UPDATE task t
SET updated_at = now() - ((t2.rn % 8) * 7 + (t2.rn % 3)) * interval '1 day',
    created_at = now() - ((t2.rn % 8) * 7 + (t2.rn % 3) + 3) * interval '1 day'
FROM ranked t2
WHERE t.id = t2.id
  AND t2.rn > (SELECT n * 0.6 FROM total);   -- keep newest 60% within the current week
SELECT 'analytics_backdated' AS entity, count(*) FROM task WHERE status = 'done';

-- ── 6. Stale claim heartbeat → attention "Stale Agent Claims" section.
--       Reaper releases dead claims (>15 min) — verify this section within
--       ~7 minutes of the backfill (mechanism working as designed). ────────
UPDATE task_claim
SET last_heartbeat_at = now() - interval '9 minutes'
WHERE state = 'active'
  AND task_id = (SELECT id FROM task WHERE title = 'Seed: claim will go stale');
SELECT 'stale_claims' AS entity, count(*) FROM task_claim
WHERE state = 'active' AND last_heartbeat_at < now() - interval '7 minutes';

\echo 'Backfill complete.'
