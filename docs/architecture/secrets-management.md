# Secrets Management — UPCP v2

## Обзор

UPCP использует абстракцию `SecretProvider` для единообразного доступа к секретам из различных бэкендов. Все секреты redact-ятся из логов, ошибок и API-ответов.

---

## SecretProvider Abstraction

```python
from abc import ABC, abstractmethod

class SecretProvider(ABC):
    """Абстрактный провайдер секретов."""

    @abstractmethod
    async def get_secret(self, key: str) -> str | None:
        """Получить значение секрета по ключу."""
        ...

    @abstractmethod
    async def get_secrets(self, keys: list[str]) -> dict[str, str | None]:
        """Получить несколько секретов за один вызов."""
        ...

    @abstractmethod
    async def set_secret(self, key: str, value: str) -> None:
        """Установить значение секрета (для провайдеров с записью)."""
        ...

    @abstractmethod
    async def delete_secret(self, key: str) -> None:
        """Удалить секрет."""
        ...
```

---

## Реализации

### EnvSecretProvider

Чтение секретов из переменных окружения. Default провайдер для development.

```python
class EnvSecretProvider(SecretProvider):
    """Чтение из os.environ с optional prefix."""

    def __init__(self, prefix: str = "UPCP_"):
        self.prefix = prefix

    async def get_secret(self, key: str) -> str | None:
        return os.environ.get(f"{self.prefix}{key}")
```

**Использование:** Development, тесты, простые Docker-развёртывания.

**Ограничения:** Нет шифрования, нет ротации, секреты в plain text.

### FileSecretProvider

Чтение секретов из файлов (по одному секрету на файл). Подходит для Docker secrets и Kubernetes secrets.

```python
class FileSecretProvider(SecretProvider):
    """Чтение из файловой системы. Один файл = один секрет."""

    def __init__(self, base_path: str = "/run/secrets"):
        self.base_path = Path(base_path)

    async def get_secret(self, key: str) -> str | None:
        secret_file = self.base_path / key
        if secret_file.exists():
            return secret_file.read_text().strip()
        return None
```

**Использование:** Docker Swarm secrets, Kubernetes Secrets (mounted as files).

### DockerSecretProvider

Специализированный провайдер для Docker Swarm secrets. Обёртка над `FileSecretProvider` с дополнительной логикой.

```python
class DockerSecretProvider(FileSecretProvider):
    """Docker Swarm secrets (/run/secrets/<name>)."""

    def __init__(self):
        super().__init__("/run/secrets")
```

### VaultSecretProvider (future)

HashiCorp Vault integration. Планируется для production deployments.

```python
class VaultSecretProvider(SecretProvider):
    """HashiCorp Vault KV v2. Пока не реализован."""

    def __init__(self, vault_url: str, auth_token: str, mount_point: str = "secret"):
        self.vault_url = vault_url
        self.auth_token = auth_token
        self.mount_point = mount_point

    async def get_secret(self, key: str) -> str | None:
        # TODO: Implement with hvac client
        raise NotImplementedError("Vault integration planned for v2.1")
```

**Статус:** Зарезервировано, не реализовано. Трекинг: UPC-F045.

---

## Провайдер по умолчанию

```python
# Configuration resolution order:
# 1. SECRET_PROVIDER env var (explicit)
# 2. If /run/secrets exists → DockerSecretProvider
# 3. Fallback → EnvSecretProvider

def create_secret_provider() -> SecretProvider:
    provider_name = os.environ.get("SECRET_PROVIDER", "auto")

    if provider_name == "env":
        return EnvSecretProvider()
    elif provider_name == "file":
        return FileSecretProvider(os.environ.get("SECRETS_PATH", "/run/secrets"))
    elif provider_name == "docker":
        return DockerSecretProvider()
    elif provider_name == "vault":
        return VaultSecretProvider(...)
    elif provider_name == "auto":
        if Path("/run/secrets").exists():
            return DockerSecretProvider()
        return EnvSecretProvider()
    else:
        raise ValueError(f"Unknown secret provider: {provider_name}")
```

---

## Encrypted Fields

### Модель

Некоторые поля в БД хранятся в зашифрованном виде. Используется `EncryptionService`:

```python
class EncryptionService:
    """AES-256-GCM шифрование полей."""

    def __init__(self, key: bytes):
        self.key = key  # 32 bytes from ENCRYPTION_KEY secret

    def encrypt(self, plaintext: str) -> str:
        """Шифрует строку, возвращает base64(ciphertext + nonce + tag)."""
        ...

    def decrypt(self, ciphertext: str) -> str:
        """Дешифрует строку."""
        ...
```

### Зашифрованные поля

| Таблица | Поле | Шифрование |
|---------|------|-----------|
| `git_provider` | `access_token_encrypted` | AES-256-GCM |
| `git_provider` | `webhook_secret_encrypted` | AES-256-GCM |
| `agent_token` | `token_hash` | bcrypt (one-way) |
| `session` | `token_hash` | bcrypt (one-way) |
| `user` | `password_hash` | bcrypt (one-way) |

### Миграция ключа

При ротации `ENCRYPTION_KEY`:

1. Старый ключ: `ENCRYPTION_KEY` (текущий)
2. Новый ключ: `ENCRYPTION_KEY_NEW`
3. Запуск миграции: `python -m upcp.cli rotate-encryption-key`
4. Скрипт перешифровывает все encrypted поля
5. После завершения: `ENCRYPTION_KEY_NEW` → `ENCRYPTION_KEY`

---

## Redaction Rules

### Автоматическая redaction

Все значения, совпадающие с паттернами секретов, автоматически заменяются на `[REDACTED]` в логах, ошибках и API-ответах.

```python
REDACTED_PATTERNS = [
    r"(?i)(password|secret|token|api_key|apikey|access_key|private_key)\s*[=:]\s*\S+",
    r"(?i)Bearer\s+\S+",
    r"(?i)X-API-Key:\s*\S+",
    r"mcp_[a-zA-Z0-9_]+",          # MCP tokens
    r"upcp_[a-zA-Z0-9_]+",         # API keys
    r"eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+",  # JWT
]
```

### Context-aware redaction

```python
class RedactionProcessor:
    """structlog processor для redaction."""

    REDACTED_KEYS = {
        "password", "password_hash", "token", "token_hash",
        "access_token", "refresh_token", "secret", "api_key",
        "encryption_key", "webhook_secret", "private_key",
    }

    def __call__(self, logger, method_name, event_dict):
        for key in list(event_dict.keys()):
            if key.lower() in self.REDACTED_KEYS:
                event_dict[key] = "[REDACTED]"
            elif isinstance(event_dict[key], str):
                event_dict[key] = self._redact_patterns(event_dict[key])
        return event_dict
```

### API Response Redaction

```python
# В middleware: перед отправкой ответа проверяем на наличие секретов
class SecretRedactionMiddleware:
    """Не допускает секреты в HTTP ответах."""

    async def __call__(self, request, call_next):
        response = await call_next(request)
        # Проверяем body на паттерны секретов
        # При обнаружении — логируем warning, заменяем на [REDACTED]
        return response
```

---

## Secret Inventory

### Required Secrets

| Secret | Назначение | Формат | Where |
|--------|-----------|--------|-------|
| `SECRET_KEY` | Session signing, CSRF | 64+ random bytes | All envs |
| `JWT_SECRET` | JWT token signing | 32+ random bytes | All envs |
| `DATABASE_URL` | PostgreSQL connection | `postgresql+asyncpg://user:pass@host:5432/db` | All envs |
| `REDIS_URL` | Redis connection | `redis://host:6379/0` | All envs |
| `ENCRYPTION_KEY` | AES-256-GCM field encryption | 32 bytes, base64 | All envs |

### Optional Secrets

| Secret | Назначение | Формат | When |
|--------|-----------|--------|------|
| `LLM_API_KEY` | LLM provider (если UPCP вызывает LLM) | Provider-specific | If LLM features enabled |
| `SMTP_PASSWORD` | Email sending | String | If email notifications enabled |
| `GITLAB_ACCESS_TOKEN` | Default GitLab integration | `glpat-...` | If GitLab configured |
| `GITHUB_ACCESS_TOKEN` | Default GitHub integration | `ghp_...` | If GitHub configured |
| `SENTRY_DSN` | Error tracking | URL | If Sentry enabled |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | OpenTelemetry collector | `http://host:4317` | If OTEL enabled |
| `ENCRYPTION_KEY_NEW` | Key rotation | 32 bytes, base64 | During rotation |

### Generated at First Boot

```python
# bootstrap_upcp.py генерирует секреты при первом запуске
SECRETS_TO_GENERATE = {
    "SECRET_KEY": {"length": 64, "format": "urlsafe_base64"},
    "JWT_SECRET": {"length": 32, "format": "urlsafe_base64"},
    "ENCRYPTION_KEY": {"length": 32, "format": "base64"},
}
```

### Secret Validation

```python
def validate_secrets() -> list[str]:
    """Проверяет наличие и валидность всех required secrets."""
    issues = []

    secret_key = secrets.get_secret("SECRET_KEY")
    if not secret_key:
        issues.append("SECRET_KEY is missing")
    elif len(secret_key) < 32:
        issues.append("SECRET_KEY is too short (min 32 chars)")

    jwt_secret = secrets.get_secret("JWT_SECRET")
    if not jwt_secret:
        issues.append("JWT_SECRET is missing")

    db_url = secrets.get_secret("DATABASE_URL")
    if not db_url:
        issues.append("DATABASE_URL is missing")
    elif not db_url.startswith("postgresql"):
        issues.append("DATABASE_URL must be a PostgreSQL connection string")

    enc_key = secrets.get_secret("ENCRYPTION_KEY")
    if not enc_key:
        issues.append("ENCRYPTION_KEY is missing")

    return issues
```

---

## Startup Checklist

```
1. Определить SECRET_PROVIDER (auto/env/file/docker)
2. Загрузить required secrets
3. Валидировать формат и длину
4. Проверить DATABASE_URL подключение
5. Проверить REDIS_URL подключение
6. Инициализировать EncryptionService
7. Проверить ENCRYPTION_KEY (дешифровка тестового значения)
8. Если есть ENCRYPTION_KEY_NEW — запустить миграцию
```
