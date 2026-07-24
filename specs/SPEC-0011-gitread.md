# SPEC-0011 Git Read Integration

Status: approved
Owner: project-owner
Milestone: M3
Related tasks: TASK-0013, TASK-0014, TASK-0017

## Problem

No git integration exists. Projects need to link branches, commits, and PRs to tasks.

## Goal

Read-only git integration: config, local adapter, task linking.

## Non-goals

- No GitHub/GitLab adapters yet (future milestone).
- No write operations (push, create branches, open PRs).
- No CI status consumption yet.

## Requirements

1. GitProvider config model: id, project_id, provider_type (local/github/gitlab), url, name, status.
2. GitBranch model: id, provider_id (FK), name, last_commit_sha, is_default.
3. GitCommit model: id, provider_id (FK), sha, message, author, committed_at.
4. GitPullRequest model: id, provider_id (FK), number, title, state, head_sha, base_branch.
5. GitLink model: id, entity_type, entity_id, git_type (branch/commit/pr), git_id.
6. LocalGitAdapter: reads branches, commits, PRs from local git repos via subprocess.
7. CRUD endpoints for config and links.
8. Query endpoints: list branches, commits, PRs for a provider.

## Acceptance Criteria

- GitProvider CRUD.
- LocalGitAdapter reads real git data.
- GitLink connects git objects to tasks.
- Coverage >= 80%.
- Migration generated.

## DoD

- Spec approved.
- Task implemented with TDD.
- All commands pass.
- Statuses updated.
