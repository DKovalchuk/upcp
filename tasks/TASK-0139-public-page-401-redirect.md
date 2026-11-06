# TASK-0139 — Public pages hard-redirect to /login by background notification infra

**Milestone:** bugfix (found via TASK-0138)
**Points:** 3
**Spec:** mini-spec (this file)
**Status:** DONE (closed 2026-10-17)

## Bug

An unauthenticated visitor on a public page (`/setup`) is yanked to
`/login` mid-page-load. Reproduced chain (probe evidence, TASK-0138):

1. `AppShell` is the ROOT route component → `NotificationBell` and
   `SSEProvider` mount on **every** route, including public `/setup`;
2. `NotificationBell` polls `notifications/unread-count` every 30s via
   `apiRequest` with **no auth gate** (`useQuery` lacks `enabled`);
3. live backend answers 401 → `client.ts:83-90` (non-`/auth/` 401, refresh
   fails, not on `/login`) → `window.location.href = '/login'`.

Same defect family, no navigation hijack but request spam:
`useSSE` connects unconditionally → 401 → reconnect backoff loop (3s→30s)
forever on public pages.

Other background refetchers (dashboard-stats 60s, attention 30s) are
protected by `AuthGuard` (pages only render authenticated) — the bell and
SSE are the only ungated pollers.

## Fix (at the source)

Gate both on auth state (`useAuth()` from `@/contexts/AuthContext`,
reactive to login/logout):

- `NotificationBell`: `enabled: isAuthenticated` on the unread-count query;
- `useSSE`: `useEffect` connects only when `isAuthenticated`, aborts on
  logout (effect cleanup already aborts).

`client.ts` 401-redirect stays as-is: it is correct for session expiry of
an authenticated user (had tokens → refresh fails → redirect). Out of
scope: changing global redirect semantics.

## TDD

Red (before fix):

1. **Root e2e (live backend)** — `tests/e2e/auth.spec.ts`: unauthenticated
   visitor (`storageState` overridden to empty) navigates to `/setup` and
   STAYS (setup form visible). Currently FAILS (redirected to /login).
2. **vitest `NotificationBell`** — unauthenticated → `fetchUnreadCount`
   NOT called; authenticated (control) → called.
3. **vitest `useSSE`** — unauthenticated → no fetch to
   `/notifications/stream`; authenticated (control) → fetch called.

Green: same tests pass after gating.

Cleanup: remove the now-dead `mockNotifications` workaround from
`frontend/e2e/auth.spec.ts` (kept heading guards) — it doubles as an
integration check: with the fix the request never happens, so the live
proxy path can't redirect either.

## AC

- [x] Root e2e: unauthenticated `/setup` stays on setup form (red → green)
      — RED confirmed before fix (page navigated to `/login` per
      error-context); GREEN 22/22 after fix
- [x] NotificationBell: no unread-count request when unauthenticated;
      requested when authenticated — `NotificationBell.test.tsx` red→green
      (2 tests)
- [x] useSSE: no stream connection when unauthenticated; connects when
      authenticated — `use-sse.test.tsx` red→green (2 tests)
- [x] `frontend/e2e/auth.spec.ts`: notification mocks removed, 6/6 still
      green (heading guards kept)
- [x] No regressions: root e2e **22/22**, frontend e2e full **153/153**,
      vitest **433/433**, lint 0 errors, tsc clean
- [x] PROJECT_STATUS Queued bug entry → closed with evidence

## Evidence

- TDD red phase: vitest `2 failed (both unauthenticated) / 2 passed
  (controls)`; root e2e regression test failed with
  "navigated to http://127.0.0.1:3072/login" (the exact bug).
- Fix: `NotificationBell.tsx` unread-count query `enabled:
  isAuthenticated`; `use-sse.ts` effect gated on `isAuthenticated`
  (cleanup aborts on logout). Green: vitest 4/4.
- **Gotcha (documented for future runs):** first root e2e run after the
  fix still failed — the dev stack frontend `upcp-frontend-1` serves a
  **pre-built `dist/`** (`serve -s dist`, no source bind-mount), i.e. the
  OLD bundle; `docker compose --env-file .env.dev build frontend && up -d
  frontend` was required before the live-stack suite could observe the
  fix → 22/22 green. Saved to project memory.
- Workaround removal: `mockNotifications` route-mocks deleted from
  frontend `auth.spec.ts` (dead post-fix), heading guards retained → 6/6.
- Full suites: root e2e 22/22 (12s), frontend e2e 153/153 (5.4m),
  vitest 433/433, lint 0 errors (3 pre-existing warnings), tsc exit 0.
