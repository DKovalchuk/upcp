# Backup & Restore — Процедуры

> Проект: UPCP | СУБД: PostgreSQL 16, Redis 7 | Среда: Docker Compose

## 1. Обзор

Резервное копирование критично для self-hosted развёртывания. Процедуры должны быть регулярными, проверенными и документированными.

## 2. PostgreSQL Backup

### 2.1 pg_dump (логический бэкап)

```bash
# Полный бэкап
docker compose exec db pg_dump -U upcp -Fc -f /tmp/upcp_$(date +%Y%m%d_%H%M%S).dump upcp

# Копировать из контейнера
docker compose cp db:/tmp/upcp_*.dump ./backups/

# Только schema
docker compose exec db pg_dump -U upcp --schema-only -f /tmp/schema.sql upcp

# Только данные (без schema)
docker compose exec db pg_dump -U upcp --data-only -f /tmp/data.sql upcp
```

### 2.2 pg_dump непрерывный (WAL archiving)

Для point-in-time recovery (PITR):

```yaml
# docker-compose.yml additions для db
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

### 2.3 Автоматический расписание

```bash
# crontab
# Ежедневный полный бэкап в 02:00
0 2 * * * cd /opt/upcp && docker compose exec -T db pg_dump -U upcp -Fc upcp | gzip > /backups/upcp_$(date +\%Y\%m\%d).dump.gz

# Ежечасный инкрементальный (WAL)
0 * * * * rsync -av /opt/upcp/wal_archive/ /backups/wal/

# Ротация: хранить 7 дней ежедневных, 30 дней еженедельных
0 3 * * * find /backups -name "upcp_*.dump.gz" -mtime +7 -delete
```

## 3. PostgreSQL Restore

### 3.1 pg_restore

```bash
# Остановить приложение
docker compose stop app

# Восстановить из бэкапа
docker compose exec db pg_restore -U upcp -d upcp --clean --if-exists /tmp/upcp_20260727.dump

# Запустить приложение
docker compose start app

# Проверить
docker compose exec app curl -f http://localhost:8000/health
```

### 3.2 Восстановление в новую БД (тест)

```bash
# Создать тестовую БД
docker compose exec db createdb -U upcp upcp_restore_test

# Восстановить
docker compose exec db pg_restore -U upcp -d upcp_restore_test /tmp/upcp_20260727.dump

# Проверить данные
docker compose exec db psql -U upcp -d upcp_restore_test -c "SELECT count(*) FROM tasks;"

# Удалить тестовую БД
docker compose exec db dropdb -U upcp upcp_restore_test
```

### 3.3 Point-in-Time Recovery

```bash
# Остановить БД
docker compose stop db

# Восстановить base backup
rm -rf pgdata/*
pg_basebackup restore...

# Настроить recovery
cat > recovery.signal << EOF
restore_command = 'cp /var/lib/postgresql/wal_archive/%f %p'
recovery_target_time = '2026-07-27 14:30:00+00'
EOF

# Запустить БД
docker compose start db
```

## 4. Redis Backup

### 4.1 RDB (снимки)

Redis автоматически делает RDB snapshots при `appendonly yes`:

```bash
# Принудительный snapshot
docker compose exec redis redis-cli BGSAVE

# Копировать RDB файл
docker compose cp redis:/data/dump.rdb ./backups/redis_$(date +%Y%m%d_%H%M%S).rdb
```

### 4.2 AOF (append-only file)

AOF включён в docker-compose (опция `--appendonly yes`):

```bash
# Копировать AOF
docker compose cp redis:/data/appendonlydir ./backups/redis_aof/

# Принудительная rewrite AOF
docker compose exec redis redis-cli BGREWRITEAOF
```

### 4.3 Restore

```bash
# Остановить Redis
docker compose stop redis

# Заменить данные
docker compose cp ./backups/redis_20260727.rdb redis:/data/dump.rdb

# Запустить
docker compose start redis

# Проверить
docker compose exec redis redis-cli DBSIZE
```

## 5. Docker Volume Backup

### 5.1 Все volumes

```bash
# Список volumes
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
# Остановить сервисы
docker compose down

# Восстановить volume
docker run --rm \
  -v upcp_pgdata:/data \
  -v $(pwd)/backups:/backup \
  alpine sh -c "cd /data && tar xzf /backup/pgdata_20260727.tar.gz"

# Запустить
docker compose up -d
```

## 6. Проверка бэкапов

### 6.1 Автоматическая верификация

```bash
#!/bin/bash
# scripts/verify-backup.sh

BACKUP_FILE=$1
TIMESTAMP=$(date +%s)
TEST_DB="upcp_verify_${TIMESTAMP}"

echo "=== Verifying backup: $BACKUP_FILE ==="

# Создать тестовую БД
docker compose exec db createdb -U upcp "$TEST_DB"

# Восстановить
docker compose exec db pg_restore -U upcp -d "$TEST_DB" "$BACKUP_FILE"
if [ $? -ne 0 ]; then
  echo "FAIL: pg_restore failed"
  docker compose exec db dropdb -U upcp "$TEST_DB"
  exit 1
fi

# Проверить таблицы
TABLES=$(docker compose exec db psql -U upcp -d "$TEST_DB" -t -c \
  "SELECT count(*) FROM information_schema.tables WHERE table_schema='public';")
echo "Tables found: $TABLES"

# Проверить миграции
CURRENT_REV=$(docker compose exec db psql -U upcp -d "$TEST_DB" -t -c \
  "SELECT version_num FROM alembic_version;")
echo "Alembic version: $CURRENT_REV"

# Cleanup
docker compose exec db dropdb -U upcp "$TEST_DB"

echo "=== Verification PASSED ==="
```

### 6.2 Расписание проверки

```bash
# Еженедельная проверка бэкапа (воскресенье 04:00)
0 4 * * 0 /opt/upcp/scripts/verify-backup.sh /backups/upcp_$(date -d 'yesterday' +\%Y\%m\%d).dump.gz
```

## 7. Скрипт полного бэкапа

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

### Экстренное восстановление (пошагово)

1. **Оценить ситуацию**: что потеряно? данные? конфигурация? всё?
2. **Остановить сервисы**: `docker compose stop app frontend nginx`
3. **Выбрать бэкап**: последний проверенный бэкап
4. **Восстановить PostgreSQL**: `pg_restore` (см. §3.1)
5. **Восстановить Redis**: копия RDB (см. §4.3)
6. **Запустить сервисы**: `docker compose up -d`
7. **Проверить**: health check, smoke test
8. **Задокументировать**: что произошло, какой бэкап использован, RTO/RPO

### RTO/RPO targets

| Метрика | Цель | Метод |
|---------|------|-------|
| RPO (Recovery Point Objective) | ≤ 24ч | Ежедневные бэкапы |
| RTO (Recovery Time Objective) | ≤ 30 мин | pg_restore + volume backup |
| RPO (с WAL archiving) | ≤ 5 мин | PITR |
