# TASK-0063 JWT Token Service

Spec: SPEC-0014
Status: done
Priority: 10
Model: routine
Milestone: M7

## Goal

Implement JWT access tokens and rotating refresh tokens for user authentication.

## Non-goals

- No auth middleware yet (TASK-0065).
- No login endpoint yet (TASK-0067).
- No agent token auth yet (TASK-0068).

## Security Requirements (per security-code-review skill)

- Access token: 15min expiry, stateless
- Refresh token: 7day expiry, DB-stored, rotating on each use
- Algorithm: HS256 (symmetric, sufficient for single-server)
- Secret key from env var UPCP_SECRET_KEY (no hardcoded defaults in prod)
- Refresh tokens invalidated when rotated
- Token fingerprint stored for replay protection

## Files likely involved

```text
backend/app/identity/token_service.py    # new
backend/app/identity/models.py           # add RefreshToken model
backend/tests/identity/test_token.py     # new
```

## TDD Steps

1. Create failing tests for token service:
   - create_access_token returns a valid JWT string
   - create_access_token payload contains sub (user_id), exp, iat, type=access
   - create_access_token with custom expiry
   - verify_access_token returns payload for valid token
   - verify_access_token raises on expired token
   - verify_access_token raises on invalid signature
   - verify_access_token raises on wrong type (refresh used as access)
   - create_refresh_token returns token string + stores in DB
   - create_refresh_token stores token fingerprint (sha256)
   - verify_refresh_token returns token record for valid token
   - verify_refresh_token raises on expired token
   - verify_refresh_token raises on revoked token
   - rotate_refresh_token invalidates old token, creates new one
   - rotate_refresh_token raises if old token already revoked
   - revoke_refresh_token marks token as revoked

2. Run tests, confirm all fail.

3. Implement RefreshToken model:
   - id: String(36), PK
   - user_id: FK → user_account.id
   - token_hash: String(64), unique (SHA-256 of token)
   - expires_at: DateTime(timezone=True)
   - revoked_at: DateTime(timezone=True), nullable
   - created_at: DateTime(timezone=True)

4. Implement TokenService:
   - create_access_token(user_id, expires_delta=None) → str
   - verify_access_token(token) → dict
   - create_refresh_token(user_id) → str
   - verify_refresh_token(token) → RefreshToken
   - rotate_refresh_token(old_token) → str
   - revoke_refresh_token(token) → None

5. Run tests, confirm all pass.

6. Generate Alembic migration for RefreshToken.

7. Run lint and typecheck.

## Acceptance Criteria

- [ ] RefreshToken model with all fields.
- [ ] TokenService with all methods.
- [ ] Access tokens are stateless JWTs.
- [ ] Refresh tokens are DB-stored with hash.
- [ ] Token rotation invalidates old, creates new.
- [ ] Expired tokens rejected.
- [ ] Revoked tokens rejected.
- [ ] Wrong token type rejected.
- [ ] Tests cover all scenarios.
- [ ] Migration generated.
- [ ] make test, make lint, make typecheck pass.
- [ ] Status updated.

## DoD

- tests added and passing;
- implementation complete;
- migration generated;
- commands pass;
- status updated.
