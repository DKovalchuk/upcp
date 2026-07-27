# Backup & Restore — Procedures

> Project: UPCP | DBMS: PostgreSQL 16, Redis 7 | Environment: Docker Compose

## 1. Overview

Backup is critical for self-hosted deployments. Procedures must be regular, tested, and documented.

## 2. PostgreSQL Backup

### 2.1 pg_dump (logical backup)

```bash
# Full backup
docker compose exec db pg_dump -U upcp -Fc -f /tmp/upcp_$(date +%Y%m%d_%H%M%S).dump upcp

# Copy from container
docker compose cp db:/tmp/upcp_*.dump ./backups/

# Schema only
docker compose exec db pg_dump -U upcp --schema-only -f /tmp/schema.sql upcp

# Data only (no schema)
docker compose exec db pg_dump -U upcp --data-only -f /tmp/data.sql upcp
```

### 2.2 pg_dump continuous (WAL archiving)

For point-in-time recovery (PITR):

```yaml
# docker-compose.yml additions for db
db:
  command: >
    postgres
    -c wal_level=replica
    -c archive_mode=on
    -c archive_command='cp %p /var/lib/postgresql/wal_archive/%f'
  volumes:
    - pgdata:/var/lib/postgresql/data
    - walarchive:/var/lib/postgresql/wal_archive
```

### 2.3 Automatic scheduling

```bash
# crontab
# Daily full backup at 02:00
0 2 * * * cd /opt/upcp && docker compose exec -T db pg_dump -U upcp -Fc upcp | gzip > /backups/upcp_$(date +\%Y\%m\%d).dump.gz

# Hourly incremental (WAL)
0 * * * * rsync -av /opt/upcp/wal_archive/ /backups/wal/

# Rotation: keep 7 days daily, 30 days weekly
0 3 * * * find /backups -name "upcp_*.dump.gz" -mtime +7 -delete
```

## 3. PostgreSQL Restore

### 3.1 pg_restore

```bash
# Stop the application
docker compose stop app

# Restore from backup
docker compose exec db pg_restore -U upcp -d upcp --clean --if-exists /tmp/upcp_20260727.dump

# Start the application
docker compose start app

# Verify
docker compose exec app curl -f http://localhost:8000/health
```

### 3.2 Restore to a new database (test)

```bash
# Create test database
docker compose exec db createdb -U upcp upcp_restore_test

# Restore
docker compose exec db pg_restore -U upcp -d upcp_restore_test /tmp/upcp_20260727.dump

# Verify data
docker compose exec db psql -U upcp -d upcp_restore_test -c "SELECT count(*) FROM tasks;"

# Drop test database
docker compose exec db dropdb -U upcp upcp_restore_test
```

### 3.3 Point-in-Time Recovery

```bash
# Stop the database
docker compose stop db

# Restore base backup
rm -rf pgdata/*
pg_basebackup restore...

# Configure recovery
cat > recovery.signal << EOF
restore_command = 'cp /var/lib/postgresql/wal_archive/%f %p'
recovery_target_time = '2026-07-27 14:30:00+00'
EOF

# Start the database
docker compose start db
```

## 4. Redis Backup

### 4.1 RDB (snapshots)

Redis automatically creates RDB snapshots when `appendonly yes`:

```bash
# Force snapshot
docker compose exec redis redis-cli BGSAVE

# Copy RDB file
docker compose cp redis:/data/dump.rdb ./backups/redis_$(date +%Y%m%d_%H%M%S).rdb
```

### 4.2 AOF (append-only file)

AOF is enabled in docker-compose (option `--appendonly yes`):

```bash
# Copy AOF
docker compose cp redis:/data/appendonlydir ./backups/redis_aof/

# Force AOF rewrite
docker compose exec redis redis-cli BGREWRITEAOF
```

### 4.3 Restore

```bash
# Stop Redis
docker compose stop redis

# Replace data
docker compose cp ./backups/redis_20260727.rdb redis:/data/dump.rdb

# Start
docker compose start redis

# Verify
docker compose exec redis redis-cli DBSIZE
```

## 5. Docker Volume Backup

### 5.1 All volumes

```bash
# List volumes
docker volume ls | grep upcp

# Backup volume
docker run --rm \
  -v upcp_pgdata:/data \
  -v $(pwd)/backups:/backup \
  alpine tar czf /backup/pgdata_$(date +%Y%m%d_%H%M%S).tar.gz -C /data .

# Backup Redis volume
docker run --rm \
  -v upcp_redisdata:/data \
  -v $(pwd)/backups:/backup \
  alpine tar czf /backup/redisdata_$(date +%Y%m%d_%H%M%S).tar.gz -C /data .
```

### 5.2 Restore volume

```bash
# Stop services
docker compose down

# Restore volume
docker run --rm \
  -v upcp_pgdata:/data \
  -v $(pwd)/backups:/backup \
  alpine sh -c "cd /data && tar xzf /backup/pgdata_20260727.tar.gz"

# Start
docker compose up -d
```

## 6. Backup verification

### 6.1 Automatic verification

```bash
#!/bin/bash
# scripts/verify-backup.sh

BACKUP_FILE=$1
TIMESTAMP=$(date +%s)
TEST_DB="upcp_verify_${TIMESTAMP}"

echo "=== Verifying backup: $BACKUP_FILE ==="

# Create test database
docker compose exec db createdb -U upcp "$TEST_DB"

# Restore
docker compose exec db pg_restore -U upcp -d "$TEST_DB" "$BACKUP_FILE"
if [ $? -ne 0 ]; then
  echo "FAIL: pg_restore failed"
  docker compose exec db dropdb -U upcp "$TEST_DB"
  exit 1
fi

# Verify tables
TABLES=$(docker compose exec db psql -U upcp -d "$TEST_DB" -t -c \
  "SELECT count(*) FROM information_schema.tables WHERE table_schema='public';")
echo "Tables found: $TABLES"

# Verify migrations
CURRENT_REV=$(docker compose exec db psql -U upcp -d "$TEST_DB" -t -c \
  "SELECT version_num FROM alembic_version;")
echo "Alembic version: $CURRENT_REV"

# Cleanup
docker compose exec db dropdb -U upcp "$TEST_DB"

echo "=== Verification PASSED ==="
```

### 6.2 Verification schedule

```bash
# Weekly backup verification (Sunday 04:00)
0 4 * * 0 /opt/upcp/scripts/verify-backup.sh /backups/upcp_$(date -d 'yesterday' +\%Y\%m\%d).dump.gz
```

## 7. Full backup script

```bash
#!/bin/bash
# scripts/backup-all.sh

set -euo pipefail
BACKUP_DIR="/backups/upcp/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo "Starting UPCP backup → $BACKUP_DIR"

# PostgreSQL
echo "Backing up PostgreSQL..."
docker compose exec -T db pg_dump -U upcp -Fc upcp > "$BACKUP_DIR/postgres.dump"

# Redis
echo "Backing up Redis..."
docker compose exec -T redis redis-cli BGSAVE
sleep 2
docker compose cp redis:/data/dump.rdb "$BACKUP_DIR/redis.rdb"

# Application config
echo "Backing up config..."
cp .env "$BACKUP_DIR/env.bak" 2>/dev/null || true
cp docker-compose*.yml "$BACKUP_DIR/"

# Compress
echo "Compressing..."
tar czf "$BACKUP_DIR.tar.gz" -C "$(dirname $BACKUP_DIR)" "$(basename $BACKUP_DIR)"
rm -rf "$BACKUP_DIR"

echo "Backup complete: $BACKUP_DIR.tar.gz ($(du -h "$BACKUP_DIR.tar.gz" | cut -f1))"
```

## 8. Restore Runbook

### Emergency restoration (step-by-step)

1. **Assess the situation**: what is lost? data? configuration? everything?
2. **Stop services**: `docker compose stop app frontend nginx`
3. **Choose backup**: the last verified backup
4. **Restore PostgreSQL**: `pg_restore` (see §3.1)
5. **Restore Redis**: RDB copy (see §4.3)
6. **Start services**: `docker compose up -d`
7. **Verify**: health check, smoke test
8. **Document**: what happened, which backup was used, RTO/RPO

### RTO/RPO targets

| Metric | Target | Method |
|---------|------|-------|
| RPO (Recovery Point Objective) | ≤ 24h | Daily backups |
| RTO (Recovery Time Objective) | ≤ 30 min | pg_restore + volume backup |
| RPO (with WAL archiving) | ≤ 5 min | PITR |
