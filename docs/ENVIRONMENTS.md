# ENVIRONMENTS

Local development environments for UPCP.

## Overview

| Environment | Frontend | Backend API | DB | Redis | Compose File |
|-------------|----------|-------------|-----|-------|--------------|
| **Stage** | http://localhost:3070 | http://localhost:38081 | 127.0.0.1:35433 | 127.0.0.1:36382 | `docker-compose.stage.yml` |
| **Dev** | http://localhost:3072 | http://localhost:38080 | 127.0.0.1:35432 | 127.0.0.1:36380 | `docker-compose.yml` |
| **Test** | http://localhost:3071 | http://localhost:38082 | 127.0.0.1:35434 | — | `docker-compose.test.yml` |

## Users

| Environment | Email | Password | Name |
|-------------|-------|----------|------|
| **Stage** | `admin@example.com` | `admin123` | Admin |
| **Dev** | `admin@dev.com` | `dev12345` | Dev Admin |
| **Test** | `admin@test.com` | `test12345` | Test Admin |

## Quick Commands

```bash
# Start all
docker compose -f docker-compose.stage.yml up -d    # stage
docker compose -f docker-compose.yml up -d           # dev
docker compose -f docker-compose.test.yml up -d      # test

# Health check
curl http://localhost:38081/health   # stage
curl http://localhost:38080/health   # dev
curl http://localhost:38082/health   # test

# Login
curl -X POST http://localhost:38081/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"admin123"}'

# Stop all
docker compose -f docker-compose.stage.yml down
docker compose -f docker-compose.yml down
docker compose -f docker-compose.test.yml down
```

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
docker compose -f docker-compose.yml exec app python -c "
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
