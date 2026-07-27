# Troubleshooting — Частые проблемы и решения

> Проект: UPCP | Среда: Docker Compose

## 1. Database Connection

### Симптом: `Connection refused` или `could not connect to server`

**Причины:**
- PostgreSQL контейнер не запущен
- Неверный `DATABASE_URL`
- Сеть Docker не поднята

**Диагностика:**
```bash
# Проверить контейнер
docker compose ps db

# Проверить логи
docker compose logs db --tail 50

# Проверить healthcheck
docker compose exec db pg_isready -U upcp

# Проверить подключение из app
docker compose exec app python -c "import asyncpg; import asyncio; asyncio.run(asyncpg.connect('postgresql://upcp:pass@db:5432/upcp'))"
```

**Решения:**
1. Запустить db: `docker compose up -d db`
2. Проверить `DATABASE_URL` в `.env` — должен быть `postgresql+asyncpg://upcp:PASSWORD@db:5432/upcp`
3. Ждать healthcheck: db может запускаться 5-10 секунд
4. Удалить volume и пересоздать (⚠️ данные потеряются): `docker compose down -v && docker compose up -d`

### Симптом: `too many connections`

**Решение:**
```bash
# Проверить текущие соединения
docker compose exec db psql -U upcp -c "SELECT count(*) FROM pg_stat_activity;"

# Настроить пул в приложении
DATABASE_MAX_CONNECTIONS=20  # в .env
```

## 2. Redis Connection

### Симптом: `Connection refused` или `Error 111`

**Диагностика:**
```bash
docker compose ps redis
docker compose logs redis --tail 20
docker compose exec redis redis-cli ping
```

**Решения:**
1. Запустить redis: `docker compose up -d redis`
2. Проверить `REDIS_URL` в `.env` — формат: `redis://redis:6379/0`
3. Проверить, что Redis слушает на нужном порту

### Симптом: `OOM command not allowed`

**Решение:**
```bash
# Проверить память
docker compose exec redis redis-cli INFO memory

# Увеличить лимит в docker-compose.yml
deploy:
  resources:
    limits:
      memory: 512M
```

## 3. Docker Build Failures

### Симптом: `COPY failed: file not found`

**Причина:** Контекст сборки не содержит нужные файлы.

**Решение:**
```bash
# Проверить .dockerignore
cat .dockerignore

# Убедиться, что файл существует
ls -la requirements.txt pyproject.toml

# Пересобрать без кеша
docker compose build --no-cache app
```

### Симптом: `pip install` timeout или ошибки сети

**Решение:**
```bash
# Использовать внутренний mirror
# В Dockerfile:
RUN pip install --index-url https://pypi.tuna.tsinghua.edu.cn/simple/

# Или увеличить таймаут
RUN pip install --timeout 120 -r requirements.txt
```

### Симптом: Out of disk space

**Решение:**
```bash
# Проверить место
df -h
docker system df

# Очистить неиспользуемые образы
docker system prune -a --volumes

# Очистить конкретно build cache
docker builder prune -a
```

## 4. Migration Errors

### Симптом: `alembic.util.exc.CommandError: Can't locate revision`

**Причина:** Несоответствие версий миграций между кодом и БД.

**Решение:**
```bash
# Проверить текущую версию
docker compose exec db psql -U upcp -c "SELECT * FROM alembic_version;"

# Применить миграции
docker compose exec app alembic upgrade head

# Если миграция сломана — downgrade и повторить
docker compose exec app alembic downgrade -1
docker compose exec app alembic upgrade head
```

### Симптом: `table already exists`

**Решение:**
```bash
# Проверить, какая таблица конфликтует
docker compose exec app alembic upgrade head 2>&1

# Stamp текущей версии (если таблицы уже созданы вручную)
docker compose exec app alembic stamp head
```

### Симптом: `column "xxx" does not exist` после миграции

**Решение:**
```bash
# Проверить, применилась ли миграция
docker compose exec db psql -U upcp -c "\d table_name"

# Принудительно применить конкретную миграцию
docker compose exec app alembic upgrade <revision>
```

## 5. Auth Issues

### Симптом: `401 Unauthorized` на всех запросах

**Диагностика:**
```bash
# Проверить JWT_SECRET
docker compose exec app env | grep JWT_SECRET

# Проверить, не истёк ли токен
python3 -c "import jwt; print(jwt.decode('YOUR_TOKEN', options={'verify_signature': False}))"
```

**Решения:**
1. Убедиться, что `JWT_SECRET` совпадает между перезапусками
2. Заново авторизоваться (получить новый access token)
3. Проверить, что `Authorization: Bearer <token>` формат правильный

### Симптом: `403 Forbidden` — нет прав

**Решение:**
```bash
# Проверить роль пользователя
docker compose exec db psql -U upcp -c "SELECT id, email, role FROM users WHERE email='user@example.com';"

# Проверить membership в проекте
docker compose exec db psql -U upcp -c "SELECT * FROM project_members WHERE user_id='USER_ID';"
```

## 6. Agent Token Issues

### Симптом: `Invalid API key`

**Диагностика:**
```bash
# Проверить ключи в БД
docker compose exec db psql -U upcp -c "SELECT id, name, prefix, is_active FROM api_keys;"

# Проверить, не отозван ли ключ
docker compose exec db psql -U upcp -c "SELECT revoked_at FROM api_keys WHERE prefix='PREFIX';"
```

**Решения:**
1. Создать новый ключ: `POST /api/v1/api-keys`
2. Убедиться, что заголовок `Authorization: ApiKey <key>`, не `Bearer`
3. Проверить, что ключ для правильного проекта

### Симптом: Agent не может claim задачу

**Решение:**
```bash
# Проверить роль агента
docker compose exec db psql -U upcp -c "SELECT role FROM api_keys WHERE prefix='PREFIX';"
# Должна быть 'agent'

# Проверить, что задача в статусе 'open'
docker compose exec db psql -U upcp -c "SELECT id, status FROM tasks WHERE id='TASK_ID';"
```

## 7. Rate Limiting

### Симптом: `429 Too Many Requests`

**Диагностика:**
```bash
# Проверить текущие лимиты
docker compose exec redis redis-cli GET "rate_limit:USER_ID"

# Проверить конфигурацию
docker compose exec app env | grep RATE_LIMIT
```

**Решения:**
1. Подождать (лимиты обычно 1 мин окно)
2. Увеличить лимит: `RATE_LIMIT_DEFAULT=120` в `.env`
3. Whitelist IP: `RATE_LIMIT_WHITELIST=10.0.0.0/8` в `.env`

## 8. Performance

### Симптом: Медленные запросы API

**Диагностика:**
```bash
# Проверить медленные запросы в PostgreSQL
docker compose exec db psql -U upcp -c "
  SELECT query, mean_exec_time, calls
  FROM pg_stat_statements
  ORDER BY mean_exec_time DESC
  LIMIT 10;"

# Проверить индексы
docker compose exec db psql -U upcp -c "
  SELECT schemaname, tablename, indexname, idx_scan
  FROM pg_stat_user_indexes
  WHERE idx_scan = 0;"
```

**Решения:**
1. Добавить индексы для часто запрашиваемых полей
2. Проверить N+1 запросы (SQLAlchemy eager loading)
3. Включить query logging: `LOG_LEVEL=DEBUG`
4. Проверить пул соединений: `DATABASE_POOL_SIZE=20`

### Симптом: Высокое потребление памяти

**Диагностика:**
```bash
docker stats --no-stream
docker compose exec app ps aux --sort=-%mem | head
```

**Решения:**
1. Ограничить memory в docker-compose: `memory: 1G`
2. Проверить утечки: `tracemalloc` в Python
3. Увеличить `GUNICORN_WORKERS` если нужна масштабируемость
