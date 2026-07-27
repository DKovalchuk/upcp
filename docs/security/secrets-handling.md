# Управление секретами — UPCP v2

> Область: `security` | Версия: 2.0.0

## 1. Принципы

1. Секреты **никогда** не попадают в логи, ответы API, ошибки, аудит-события
2. Секреты хранятся только через `SecretProvider`
3. В БД — только зашифрованные значения
4. Все секреты валидируются при старте приложения
5. Ротация секретов — штатная операция

## 2. SecretProvider

Абстракция для получения секретов. Единый интерфейс, несколько реализаций.

```python
class SecretProvider(Protocol):
    def get(self, key: str) -> str | None: ...
    def get_required(self, key: str) -> str: ...
    def set(self, key: str, value: str) -> None: ...
    def delete(self, key: str) -> None: ...
    def list_keys(self, prefix: str = "") -> list[str]: ...
```

### 2.1 Реализации

| Провайдер              | Использование                     |
|-----------------------|-----------------------------------|
| `EnvSecretProvider`   | Переменные окружения (dev/stage)  |
| `VaultSecretProvider` | HashiCorp Vault (production)      |
| `FileSecretProvider`  | Зашифрованный файл (self-hosted)  |

### 2.2 Выбор провайдера

```python
# app/config.py
SECRET_BACKEND = os.getenv("SECRET_BACKEND", "env")  # env | vault | file
```

### 2.3 Обязательные ключи

| Ключ                           | Описание                           |
|-------------------------------|-----------------------------------|
| `DATABASE_URL`                | URL подключения к PostgreSQL       |
| `REDIS_URL`                   | URL подключения к Redis            |
| `JWT_PRIVATE_KEY`             | RS256 приватный ключ              |
| `JWT_PUBLIC_KEY`              | RS256 публичный ключ              |
| `ENCRYPTION_KEY`              | AES-256 ключ шифрования полей     |
| `SECRET_KEY`                  | Общий ключ приложения (HMAC)       |

## 3. Запрет на утечки секретов

### 3.1 Логирование

- Все логи проходят через `RedactingLogger`
- Автоматическое удаление паттернов: API keys, tokens, passwords, connection strings
- Ручная проверка при добавлении новых полей в логи

Запрещённые паттерны в логах:

```
password, secret, token, api_key, private_key,
authorization, cookie, credentials, DATABASE_URL,
REDIS_URL, ENCRYPTION_KEY
```

### 3.2 API Responses

- Ни одно поле, содержащее секрет, не возвращается в API
- Даже в `500 Internal Server Error` — нет деталей конфигурации
- Debug endpoints отключены в production

### 3.3 Обработка ошибок

```python
# ✅ Правильно
raise AppError("Database connection failed")

# ❌ Неправильно
raise AppError(f"Cannot connect to {DATABASE_URL}")
```

## 4. Шифрованные поля в БД

### 4.1 Механизм

- Алгоритм: AES-256-GCM
- Ключ: `ENCRYPTION_KEY` из SecretProvider
- Каждое значение шифруется с уникальным IV
- Формат: `v1:{base64_iv}:{base64_ciphertext}:{base64_tag}`

### 4.2 Зашифрованные поля

| Таблица           | Поле                      | Причина                  |
|------------------|--------------------------|--------------------------|
| `agent_tokens`    | `token_hash`             | Токен агента             |
| `refresh_tokens`  | `token_hash`             | Refresh token            |
| `integrations`    | `credentials_encrypted`  | API keys интеграций      |
| `projects`        | `settings_encrypted`     | Настройки с секретами    |
| `users`           | `password_hash`          | Пароль (bcrypt, не AES)  |

### 4.3 Индексация

Зашифрованные поля нельзя индексировать напрямую.
Для поиска: хеш-индекс (SHA-256 от plaintext) хранится отдельно.

```sql
-- token_hash_index для быстрого поиска refresh tokens
CREATE INDEX idx_refresh_tokens_hash
ON refresh_tokens (token_hash_index);
```

## 5. Redaction Layer

### 5.1 RedactingSerializer

Все объекты перед отправкой в лог/API проходят через redaction:

```python
REDACTED_FIELDS = {
    "password", "secret", "token", "api_key",
    "private_key", "credentials", "authorization",
    "cookie", "encryption_key",
}

REDACTED_PATTERNS = [
    r"(?i)(password|secret|token|key)\s*[:=]\s*\S+",
    r"Bearer\s+\S+",
    r"postgresql://\S+:\S+@",
    r"redis://\S+:\S+@",
]
```

### 5.2 Применение

- Все логи → `RedactingHandler`
- Все API error responses → `redact_error()`
- Все audit events → `redact_audit_event()`
- Все debug output → `redact_debug()`

## 6. Ротация секретов

### 6.1 Ротация ENCRYPTION_KEY

1. Новый ключ генерируется
2. Все зашифрованные поля перешифровываются (background migration)
3. Старый ключ помечается как `previous`
4. После завершения миграции старый ключ удаляется

### 6.2 Ротация JWT ключей

1. Новая пара RS256 генерируется
2. Публикуется JWKS endpoint с обоими ключами (kid)
3. Новые токены подписываются новым ключом
4. Через 24 часа старый ключ удаляется из JWKS

### 6.3 Ротация паролей сервисов

- PostgreSQL: через SecretProvider + перезапуск приложения
- Redis: через SecretProvider + перезапуск приложения
- Graceful shutdown позволяет завершить активные запросы

## 7. Валидация при старте

```python
# Приложение НЕ СТАРТУЕТ без валидных секретов
async def validate_secrets_on_startup():
    provider = get_secret_provider()

    # Проверяем наличие обязательных ключей
    for key in REQUIRED_SECRETS:
        value = provider.get_required(key)
        validate_format(key, value)

    # Проверяем подключение к БД
    await check_database_connection()

    # Проверяем подключение к Redis
    await check_redis_connection()

    # Проверяем JWT ключи
    validate_jwt_keypair()
```

## 8. Обработка компрометации

При обнаружении утечки секрета:

1. **Немедленно** отзываются все затронутые токены
2. Секрет ротируется через SecretProvider
3. Инцидент логируется в аудит-систему
4. Уведомляется владелец проекта/организации
5. Проводится ревью логов на предмет несанкционированного доступа
