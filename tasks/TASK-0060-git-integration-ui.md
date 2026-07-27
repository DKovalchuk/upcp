# TASK-0060: Git Integration UI

**Status**: done
**Spec**: SPEC-0011
**Phase**: Future
**Depends on**: TASK-0046
**Estimated effort**: 2-3 hours

---

## Problem

Backend has gitread endpoints (providers, branches, commits, links) but no frontend UI to view or manage them.

## Scope

1. Create TypeScript types for GitProvider, GitBranch, GitCommit, GitLink
2. Create API functions in api.ts for git endpoints
3. Create React hooks: useGitProviders, useGitBranches, useGitCommits
4. Create GitIntegrationPage component with:
   - List of git providers with status
   - Branches table per provider
   - Recent commits per provider
   - Link/unlink tasks to git objects
5. Add "Git" tab to ProjectDetail
6. Add route for /projects/:id/git

## Acceptance Criteria

- [ ] Git types exist in types/git.ts
- [ ] API functions for git endpoints exist
- [ ] React hooks for git data exist
- [ ] GitIntegrationPage shows providers, branches, commits
- [ ] "Git" tab appears in ProjectDetail
- [ ] Create/delete provider works
- [ ] `npm run build` passes
- [ ] Tests pass
