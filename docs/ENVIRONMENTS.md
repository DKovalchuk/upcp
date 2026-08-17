# ENVIRONMENTS

Local development environments for UPCP.

## Port Configuration

Ports are configured via per-environment `.env` files. Each file defines all external-facing ports:

| File | Environment | Frontend | Backend | DB | Redis |
|------|-------------|----------|---------|-----|-------|
| `.env.dev` | Dev | 3072 | 38080 | 35432 | 36380 |
| `.env.test` | Test | 3071 | 38082 | 35434 | — |
| `.env.stage` | Stage | 3070 | 38081 | 35433 | 36382 |

**To change a port:** edit the corresponding `.env.*` file. No code changes needed.

**Override at runtime:**
```bash
UPCP_PORT_FRONTEND=4000 docker compose --env-file .env.dev up -d
```

## Quick Commands

```bash
# Start with env file
docker compose --env-file .env.stage up -d    # stage
docker compose --env-file .env.dev up -d      # dev
docker compose --env-file .env.test up -d     # test

# Health check (ports from .env.* files)
curl http://localhost:38081/health   # stage (default)
curl http://localhost:38080/health   # dev (default)
curl http://localhost:38082/health   # test (default)

# Login
curl -X POST http://localhost:38081/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"admin123"}'

# Stop all
docker compose --env-file .env.stage down
docker compose --env-file .env.dev down
docker compose --env-file .env.test down
```

## Users

| Environment | Email | Password | Name |
|-------------|-------|----------|------|
| **Stage** | `admin@example.com` | `admin123` | Admin |
| **Dev** | `admin@dev.com` | `dev12345` | Dev Admin |
| **Test** | `admin@test.com` | `test12345` | Test Admin |

## Environment Differences

| Feature | Stage | Dev | Test |
|---------|-------|-----|------|
| Hot reload | No | Yes (volume mount) | No |
| Redis | Yes | Yes | No |
| Nginx | Dockerfile.nginx | nginx.dev.conf | nginx.test.conf |
| UPCP_ENV | stage | local | test |
| Log level | INFO | INFO | INFO |

## Notes

- **Stage**: Production-like. Rebuilt from `develop` branch via CI deploy job. Images pulled from GitLab registry.
- **Dev**: Local development. Backend source mounted as volume for hot reload. Frontend also mounted.
- **Test**: CI/CD testing. Built from Dockerfiles. No Redis (stateless backend tests).

## Adding New Users

Setup endpoint is rate-limited (1 per 24h). To add users manually:

```bash
# Via Docker exec
docker compose --env-file .env.dev exec app python -c "
import bcrypt
from sqlalchemy import text
from app.shared.database import engine
pwd = bcrypt.hashpw(b'PASSWORD', bcrypt.gensalt()).decode()
with engine.connect() as conn:
    conn.execute(text(
        \"INSERT INTO user_account (id, email, display_name, password_hash, is_active, is_superuser, email_verified, failed_login_attempts, created_at, updated_at) VALUES (gen_random_uuid()::text, 'EMAIL', 'NAME', :pw, true, false, true, 0, now(), now())\"
    ), {'pw': pwd})
    conn.commit()
    print('User created')
"
```
