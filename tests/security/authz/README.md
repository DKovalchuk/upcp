# Auth/RBAC security suite (TASK-0142 / SPEC-0024 Phase 4)

Integration checks against the **live test stack** (auth ON) — not the
`backend/tests` unit suite (which runs with `UPCP_DISABLE_AUTH=true`).

## How to run

From the repo root (the `-o addopts=` neutralizes root `pyproject.toml`
`addopts` with `--cov`; **verified** — see contract below):

```bash
python -m pytest tests/security/authz -o addopts= -q --junitxml /tmp/authz.xml
echo $?   # 0 = green, 1 = failures (plain pytest exit codes)

# Optional shared result document (schema upcp-security-result/v1):
SECURITY_RESULT_OUT=tests/security/results/authz.json \
  python -m pytest tests/security/authz -o addopts= -q
```

Run `python -m pytest …` (not bare `pytest`): the suite imports
`tests.security.common` via the repo-root cwd on `sys.path`.

Optional environment: `SECURITY_BASE_URL` (default `http://localhost:38082`),
`UPCP_SECRET_KEY` (forged-JWT probes; default matches `docker-compose.test.yml`),
`SECURITY_DB_*` (member-user discovery; defaults match `.env.test` ports/creds).
Host deps beyond `tests/security/requirements.txt`: `psycopg` (member RBAC
checks — without it those tests skip), `ruff` for linting.

## Result document

One collected test = one check. Written only when `SECURITY_RESULT_OUT` is set.

| pytest outcome | check `status` | notes |
| --- | --- | --- |
| passed | `pass` | xpass noted in `detail` |
| failed | `fail` | `detail` = assertion message; `severity` = marker (`high` for auth-bypass/rbac class, else `medium`) |
| xfail (`strict=False`) | `fail` | `detail` = `xfail (known finding): …` — known gaps surface as findings, pytest stays green; also listed in top-level `xfailed` |
| skipped | — | listed in top-level `skipped` (a pass/fail-only schema cannot represent it) |

## Coverage matrix

| Area | Positive | Negative | Boundary |
| --- | --- | --- | --- |
| Tokens | valid JWT → `/auth/me` 200; minted JWT accepted (secret wiring) | missing/garbage bearer, wrong signature, `type=refresh`, nonexistent subject → 401 | expired-but-signed JWT → 401 |
| Refresh | rotation issues new pair; chain hop 2 works | reused old refresh → 401; garbage → 401 | — |
| Logout | — | logout → refresh 401; logout requires auth | access survives logout (xfail finding) |
| Auth bypass | 12 endpoints × valid JWT → not 401/403 | same 12 × anonymous → 401; malformed `Authorization`, garbage `X-Agent-Token` → 401 | documented-public `/health`, `/api/v1/health` → 200 |
| RBAC | owner creates/revokes agent token (201/200); member reads agents; fresh agent token → `/api/v1/agent/me` 200 | member create/revoke token → 403; revoked agent token → 401 | Member `update:project` unenforced (xfail finding) |
| Password | — | wrong current → 400; unauthenticated → 401 | weak new password → 422 |
| Lockout | — | **skipped** (see below) | — |

## Known findings (xfail, `strict=False` — recorded as failed checks)

1. `test_nonexistent_user_rejected_on_domain_endpoint` — middleware checks only
   the signature; routes without `get_current_user` (e.g. `GET /api/v1/projects`)
   accept a correctly-signed token for a nonexistent/deleted subject until `exp`.
2. `test_access_token_rejected_after_logout` — logout revokes the refresh token
   only; the access JWT stays valid until `exp` (stateless, 15-min window).
3. `test_member_update_project_enforces_role` — seeded RBAC roles are never
   enforced: domain routes answer 404 (resource lookup) where RBAC intent is 403.

## Limitations

- **Lockout not executed**: 5 failed logins would lock the shared
  `admin@example.com` for 30 min; `POST /auth/setup` is single-use (409), so no
  disposable account can be created — test is `skip`-marked with the reason.
- **Second (member) identity** is a seeded non-superuser user discovered via a
  **read-only** DB query (no HTTP user-listing endpoint exists); its JWT is
  minted with the test-stack secret. Skips gracefully if DB/psycopg unavailable.
- No password-change success path (would mutate the shared password); no
  inactive-user probe (not settable without mutating the DB — the same code
  branch is covered by the nonexistent-subject check).
- Rate-limit `429` is out of scope: `UPCP_DISABLE_RATE_LIMIT=true` on this stack.
- `PUBLIC_PATHS` lists `/mcp/health`, which is not a registered route (404);
  harmless, not asserted here.
