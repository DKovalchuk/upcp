# Модель угроз — UPCP v2 (STRIDE)

> Область: `security` | Версия: 2.0.0

## 1. Обзор

Модель угроз построена по методологии STRIDE. Каждая угроза: описание, вектор атаки, воздействие, митигация.

## 2. Контекст системы

```
Browser/React 19 → FastAPI (Python 3.12) → PostgreSQL
                       ↓
                     Redis
                       ↓
                  AI Agents (MCP)
```

## 3. Spoofing (Подмена)

**S1: Подмена агента через украденный токен**
- Вектор: утечка agent token из CI/CD, env, логов → имперсонатор выполняет задачи
- Митигация: SecretProvider, scope restriction (токен привязан к проекту), ротация 30 дней, audit event при каждом использовании

**S2: Подмена пользователя через украденную сессию**
- Вектор: XSS → кража access token, или украденный refresh token
- Митигация: access token только в памяти (не localStorage), refresh token httpOnly/Secure/SameSite=Strict, CSP headers, token rotation, reuse detection (повторный отзыванный refresh → отзыв всей цепочки)

**S3: Credential stuffing**
- Вектор: массовые попытки входа с украденными credentials
- Митигация: rate limit 5 попыток/мин/IP, lockout 15 мин после 5 fail, проверка breached passwords (HaveIBeenPwned, k-anonymity)

## 4. Tampering (Подделка)

**T1: Модификация задач/результатов агентами**
- Вектор: агент с избыточными правами изменяет чужие задачи
- Митигация: агент работает только с claimed задачами, immutable после submit, hash-цепочка аудит-лога, reviewer approve/reject

**T2: Инъекция через MCP инструменты**
- Вектор: prompt injection → произвольные MCP вызовы
- Митигация: allowlist инструментов, валидация/sanitизация аргументов, rate limit 200/мин/токен, audit log с аргументами, изоляция MCP серверов (отдельные контейнеры)

**T3: SQL injection**
- Вектор: вредоносный ввод через API
- Митигация: SQLAlchemy 2 ORM (параметризованные запросы), Pydantic валидация, запрет raw SQL, минимальные привилегии DB user

## 5. Repudiation (Отрицание)

**R1: Невозможность доказать действие**
- Вектор: пользователь отрицает действие
- Митигация: полный audit log (timestamp, actor, IP, user_agent), append-only с hash-цепочкой, retention 12 мес + архив, отдельный service account для записи

**R2: Пробелы в аудите**
- Вектор: действия не попадают в аудит-лог
- Митигация: тесты покрытия аудит-событий, мониторинг падения event count, регулярное сравнение API endpoints с audit coverage

## 6. Information Disclosure (Раскрытие информации)

**I1: Утечка секретов через API**
- Вектор: ошибки возвращают секреты в ответах
- Митигация: redaction layer на всех ответах, запрет полей password/token/secret, тесты, error handler без stack trace в production

**I2: Утечка секретов через логи**
- Вектор: логи содержат пароли, токены, connection strings
- Митигация: RedactingLogger с паттерн-матчингом, запрет логирования password/token/secret/key, code review, автоматический скан логов

**I3: Cross-project доступ агента**
- Вектор: агент запрашивает данные вне scope проекта
- Митигация: scope enforcement на уровне middleware (token.project_id == resource.project_id), audit event при попытке

**I4: SQL errors с деталями схемы**
- Вектор: необработанные SQL exceptions в ответах
- Митигация: global exception handler (generic error), детали только в логах, тесты

## 7. Denial of Service

**D1: API abuse / rate limiting bypass**
- Митигация: rate limiting по IP/user/agent/token (см. `rate-limiting.md`), abuse detection с блокировкой, connection pooling, request timeout 30 сек (API) / 10 сек (auth)

**D2: Resource exhaustion через агентов**
- Митигация: лимит 10 задач в работе на агента, файлы ≤50 МБ, ≤1000 файлов на проект, timeout задач 30 мин

**D3: Database overload**
- Митигация: обязательная пагинация (max 100), query timeout 10 сек, connection pool 5–20, read replicas (future)

## 8. Elevation of Privilege

**E1: RBAC bypass через API**
- Митигация: проверка прав на каждом эндпоинте (decorator-based), middleware: auth → authz → handler, default deny, тесты каждой роли на каждом эндпоинте

**E2: Ролевая манипуляция**
- Вектор: пользователь назначает себе более высокую роль
- Митигация: назначение ролей только с `admin.role.assign`, один Owner на organization, self-role-change запрещён, audit event при смене

**E3: Agent token escalation**
- Вектор: агент пытается получить права выше роли
- Митигация: фиксированная роль после создания токена, scope enforcement, макс. роль агента: Member (никогда Admin/Owner), audit при попытке

## 9. Матрица рисков

| ID  | Угроза                     | Вероятность | Воздействие | Риск    | Митигация  |
|-----|----------------------------|:-----------:|:-----------:|:-------:|:----------:|
| S1  | Подмена агента             | Средняя     | Высокое     | Высокий | ✅ Done    |
| S2  | Подмена пользователя       | Низкая      | Критич.     | Высокий | ✅ Done    |
| S3  | Credential stuffing        | Средняя     | Среднее     | Средний | ✅ Done    |
| T1  | Модификация задач          | Низкая      | Среднее     | Средний | ✅ Done    |
| T2  | MCP prompt injection       | Высокая     | Высокое     | Высокий | ⚠️ Partial |
| T3  | SQL injection              | Низкая      | Критич.     | Высокий | ✅ Done    |
| R1  | Отрицание действий         | Средняя     | Низкое      | Низкий  | ✅ Done    |
| R2  | Пробелы в аудите           | Средняя     | Среднее     | Средний | ⚠️ Partial |
| I1  | Утечка секретов (API)      | Низкая      | Критич.     | Высокий | ✅ Done    |
| I2  | Утечка секретов (логи)     | Средняя     | Высокое     | Высокий | ✅ Done    |
| I3  | Cross-project доступ       | Низкая      | Высокое     | Средний | ✅ Done    |
| I4  | SQL errors                 | Низкая      | Низкое      | Низкий  | ✅ Done    |
| D1  | API abuse                  | Высокая     | Среднее     | Средний | ✅ Done    |
| D2  | Resource exhaustion        | Средняя     | Среднее     | Средний | ✅ Done    |
| D3  | Database overload          | Низкая      | Высокое     | Средний | ⚠️ Partial |
| E1  | RBAC bypass                | Низкая      | Критич.     | Высокий | ✅ Done    |
| E2  | Ролевая манипуляция        | Низкая      | Критич.     | Высокий | ✅ Done    |
| E3  | Agent token escalation     | Низкая      | Высокое     | Средний | ✅ Done    |
