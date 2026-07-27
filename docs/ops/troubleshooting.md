# Troubleshooting — Common Issues and Solutions

> Project: UPCP | Environment: Docker Compose

## 1. Database Connection

### Symptom: `Connection refused` or `could not connect to server`

**Causes:**
- PostgreSQL container is not running
- Incorrect `DATABASE_URL`
- Docker network is not up

**Diagnostics:**
```bash
# Check container status
docker compose ps db

# Check logs
docker compose logs db --tail 50

# Check healthcheck
docker compose exec db pg_isready -U upcp

# Check connection from app
docker compose exec app python -c "import asyncpg; import asyncio; asyncio.run(asyncpg.connect('postgresql://upcp:pass@db:5432/upcp'))"
```

**Solutions:**
1. Start db: `docker compose up -d db`
2. Verify `DATABASE_URL` in `.env` — should be `postgresql+asyncpg://upcp:PASSWORD@db:5432/upcp`
3. Wait for healthcheck: db may take 5-10 seconds to start
4. Remove volume and recreate (⚠️ data will be lost): `docker compose down -v && docker compose up -d`

### Symptom: `too many connections`

**Solution:**
```bash
# Check current connections
docker compose exec db psql -U upcp -c "SELECT count(*) FROM pg_stat_activity;"

# Configure pool in application
DATABASE_MAX_CONNECTIONS=20  # in .env
```

## 2. Redis Connection

### Symptom: `Connection refused` or `Error 111`

**Diagnostics:**
```bash
docker compose ps redis
docker compose logs redis --tail 20
docker compose exec redis redis-cli ping
```

**Solutions:**
1. Start redis: `docker compose up -d redis`
2. Verify `REDIS_URL` in `.env` — format: `redis://redis:6379/0`
3. Check that Redis is listening on the correct port

### Symptom: `OOM command not allowed`

**Solution:**
```bash
# Check memory
docker compose exec redis redis-cli INFO memory

# Increase limit in docker-compose.yml
deploy:
  resources:
    limits:
      memory: 512M
```

## 3. Docker Build Failures

### Symptom: `COPY failed: file not found`

**Cause:** Build context does not contain the required files.

**Solution:**
```bash
# Check .dockerignore
cat .dockerignore

# Verify that the file exists
ls -la requirements.txt pyproject.toml

# Rebuild without cache
docker compose build --no-cache app
```

### Symptom: `pip install` timeout or network errors

**Solution:**
```bash
# Use an internal mirror
# In Dockerfile:
RUN pip install --index-url https://pypi.tuna.tsinghua.edu.cn/simple/

# Or increase timeout
RUN pip install --timeout 120 -r requirements.txt
```

### Symptom: Out of disk space

**Solution:**
```bash
# Check disk space
df -h
docker system df

# Remove unused images
docker system prune -a --volumes

# Remove build cache specifically
docker builder prune -a
```

## 4. Migration Errors

### Symptom: `alembic.util.exc.CommandError: Can't locate revision`

**Cause:** Migration version mismatch between code and database.

**Solution:**
```bash
# Check current version
docker compose exec db psql -U upcp -c "SELECT * FROM alembic_version;"

# Apply migrations
docker compose exec app alembic upgrade head

# If migration is broken — downgrade and retry
docker compose exec app alembic downgrade -1
docker compose exec app alembic upgrade head
```

### Symptom: `table already exists`

**Solution:**
```bash
# Check which table is conflicting
docker compose exec app alembic upgrade head 2>&1

# Stamp current version (if tables were already created manually)
docker compose exec app alembic stamp head
```

### Symptom: `column "xxx" does not exist` after migration

**Solution:**
```bash
# Check if migration was applied
docker compose exec db psql -U upcp -c "\d table_name"

# Force apply a specific migration
docker compose exec app alembic upgrade <revision>
```

## 5. Auth Issues

### Symptom: `401 Unauthorized` on all requests

**Diagnostics:**
```bash
# Check JWT_SECRET
docker compose exec app env | grep JWT_SECRET

# Check if token has expired
python3 -c "import jwt; print(jwt.decode('YOUR_TOKEN', options={'verify_signature': False}))"
```

**Solutions:**
1. Ensure `JWT_SECRET` is consistent across restarts
2. Re-authenticate (obtain a new access token)
3. Verify that `Authorization: Bearer <token>` format is correct

### Symptom: `403 Forbidden` — insufficient permissions

**Solution:**
```bash
# Check user role
docker compose exec db psql -U upcp -c "SELECT id, email, role FROM users WHERE email='user@example.com';"

# Check project membership
docker compose exec db psql -U upcp -c "SELECT * FROM project_members WHERE user_id='USER_ID';"
```

## 6. Agent Token Issues

### Symptom: `Invalid API key`

**Diagnostics:**
```bash
# Check keys in database
docker compose exec db psql -U upcp -c "SELECT id, name, prefix, is_active FROM api_keys;"

# Check if key has been revoked
docker compose exec db psql -U upcp -c "SELECT revoked_at FROM api_keys WHERE prefix='PREFIX';"
```

**Solutions:**
1. Create a new key: `POST /api/v1/api-keys`
2. Ensure the header is `Authorization: ApiKey <key>`, not `Bearer`
3. Verify the key belongs to the correct project

### Symptom: Agent cannot claim a task

**Solution:**
```bash
# Check agent role
docker compose exec db psql -U upcp -c "SELECT role FROM api_keys WHERE prefix='PREFIX';"
# Should be 'agent'

# Check that task is in 'open' status
docker compose exec db psql -U upcp -c "SELECT id, status FROM tasks WHERE id='TASK_ID';"
```

## 7. Rate Limiting

### Symptom: `429 Too Many Requests`

**Diagnostics:**
```bash
# Check current limits
docker compose exec redis redis-cli GET "rate_limit:USER_ID"

# Check configuration
docker compose exec app env | grep RATE_LIMIT
```

**Solutions:**
1. Wait (limits typically use a 1-minute window)
2. Increase limit: `RATE_LIMIT_DEFAULT=120` in `.env`
3. Whitelist IP: `RATE_LIMIT_WHITELIST=10.0.0.0/8` in `.env`

## 8. Performance

### Symptom: Slow API requests

**Diagnostics:**
```bash
# Check slow queries in PostgreSQL
docker compose exec db psql -U upcp -c "
  SELECT query, mean_exec_time, calls
  FROM pg_stat_statements
  ORDER BY mean_exec_time DESC
  LIMIT 10;"

# Check indexes
docker compose exec db psql -U upcp -c "
  SELECT schemaname, tablename, indexname, idx_scan
  FROM pg_stat_user_indexes
  WHERE idx_scan = 0;"
```

**Solutions:**
1. Add indexes for frequently queried fields
2. Check for N+1 queries (SQLAlchemy eager loading)
3. Enable query logging: `LOG_LEVEL=DEBUG`
4. Check connection pool: `DATABASE_POOL_SIZE=20`

### Symptom: High memory usage

**Diagnostics:**
```bash
docker stats --no-stream
docker compose exec app ps aux --sort=-%mem | head
```

**Solutions:**
1. Limit memory in docker-compose: `memory: 1G`
2. Check for leaks: `tracemalloc` in Python
3. Increase `GUNICORN_WORKERS` if scalability is needed
