# Secrets Management — UPCP v2

> Scope: `security` | Version: 2.0.0

## 1. Principles

1. Secrets **never** appear in logs, API responses, errors, audit events
2. Secrets are stored only via `SecretProvider`
3. In the database — encrypted values only
4. All secrets are validated on application startup
5. Secret rotation is a routine operation

## 2. SecretProvider

Abstraction for retrieving secrets. Single interface, multiple implementations.

```python
class SecretProvider(Protocol):
    def get(self, key: str) -> str | None: ...
    def get_required(self, key: str) -> str: ...
    def set(self, key: str, value: str) -> None: ...
    def delete(self, key: str) -> None: ...
    def list_keys(self, prefix: str = "") -> list[str]: ...
```

### 2.1 Implementations

| Provider                | Use Case                        |
|------------------------|---------------------------------|
| `EnvSecretProvider`    | Environment variables (dev/stage)|
| `VaultSecretProvider`  | HashiCorp Vault (production)    |
| `FileSecretProvider`   | Encrypted file (self-hosted)    |

### 2.2 Provider Selection

```python
# app/config.py
SECRET_BACKEND = os.getenv("SECRET_BACKEND", "env")  # env | vault | file
```

### 2.3 Required Keys

| Key                            | Description                        |
|--------------------------------|------------------------------------|
| `DATABASE_URL`                 | PostgreSQL connection URL          |
| `REDIS_URL`                    | Redis connection URL               |
| `JWT_PRIVATE_KEY`              | RS256 private key                 |
| `JWT_PUBLIC_KEY`               | RS256 public key                  |
| `ENCRYPTION_KEY`               | AES-256 field encryption key      |
| `SECRET_KEY`                   | Application shared key (HMAC)     |

## 3. Secret Leakage Prevention

### 3.1 Logging

- All logs pass through `RedactingLogger`
- Automatic removal of patterns: API keys, tokens, passwords, connection strings
- Manual review required when adding new fields to logs

Forbidden patterns in logs:

```
password, secret, token, api_key, private_key,
authorization, cookie, credentials, DATABASE_URL,
REDIS_URL, ENCRYPTION_KEY
```

### 3.2 API Responses

- No field containing a secret is returned in the API
- Even in `500 Internal Server Error` — no configuration details
- Debug endpoints are disabled in production

### 3.3 Error Handling

```python
# ✅ Correct
raise AppError("Database connection failed")

# ❌ Incorrect
raise AppError(f"Cannot connect to {DATABASE_URL}")
```

## 4. Encrypted Fields in the Database

### 4.1 Mechanism

- Algorithm: AES-256-GCM
- Key: `ENCRYPTION_KEY` from SecretProvider
- Each value is encrypted with a unique IV
- Format: `v1:{base64_iv}:{base64_ciphertext}:{base64_tag}`

### 4.2 Encrypted Fields

| Table             | Field                     | Reason                   |
|-------------------|---------------------------|--------------------------|
| `agent_tokens`    | `token_hash`              | Agent token              |
| `refresh_tokens`  | `token_hash`              | Refresh token            |
| `integrations`    | `credentials_encrypted`   | Integration API keys     |
| `projects`        | `settings_encrypted`      | Settings with secrets    |
| `users`           | `password_hash`           | Password (bcrypt, not AES)|

### 4.3 Indexing

Encrypted fields cannot be indexed directly.
For search: a hash index (SHA-256 of plaintext) is stored separately.

```sql
-- token_hash_index for fast refresh token lookups
CREATE INDEX idx_refresh_tokens_hash
ON refresh_tokens (token_hash_index);
```

## 5. Redaction Layer

### 5.1 RedactingSerializer

All objects pass through redaction before being sent to logs/API:

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

### 5.2 Application

- All logs → `RedactingHandler`
- All API error responses → `redact_error()`
- All audit events → `redact_audit_event()`
- All debug output → `redact_debug()`

## 6. Secret Rotation

### 6.1 ENCRYPTION_KEY Rotation

1. New key is generated
2. All encrypted fields are re-encrypted (background migration)
3. Old key is marked as `previous`
4. After migration completes, old key is deleted

### 6.2 JWT Key Rotation

1. New RS256 key pair is generated
2. JWKS endpoint is published with both keys (kid)
3. New tokens are signed with the new key
4. After 24 hours, the old key is removed from JWKS

### 6.3 Service Password Rotation

- PostgreSQL: via SecretProvider + application restart
- Redis: via SecretProvider + application restart
- Graceful shutdown allows active requests to complete

## 7. Startup Validation

```python
# Application does NOT START without valid secrets
async def validate_secrets_on_startup():
    provider = get_secret_provider()

    # Verify required keys exist
    for key in REQUIRED_SECRETS:
        value = provider.get_required(key)
        validate_format(key, value)

    # Verify database connection
    await check_database_connection()

    # Verify Redis connection
    await check_redis_connection()

    # Verify JWT keys
    validate_jwt_keypair()
```

## 8. Compromise Handling

When a secret leak is detected:

1. **Immediately** revoke all affected tokens
2. Rotate the secret via SecretProvider
3. Log the incident to the audit system
4. Notify the project/organization owner
5. Review logs for unauthorized access
