import re
from dataclasses import dataclass
from typing import Any

from app.audit.service import AuditService
from app.shared.text import new_id


@dataclass
class RedactionResult:
    """Result of redaction process."""
    redacted_text: str
    redaction_count: int
    redaction_types: list[str]


class Redactor:
    """Redact secrets from text before sending to LLM."""
    
    # Regex patterns for different secret types
    PATTERNS = {
        "api_key": [
            re.compile(r"(?i)(api[_-]?key\s*[:=]\s*['\"]?)([A-Za-z0-9_\-]{20,})(['\"]?)"),
            re.compile(r"(?i)(key\s*[:=]\s*['\"]?)([A-Za-z0-9_\-]{20,})(['\"]?)"),
        ],
        "password": [
            re.compile(r"(?i)(password\s*[:=]\s*['\"]?)([^\s'\"]{8,})(['\"]?)"),
            re.compile(r"(?i)(passwd\s*[:=]\s*['\"]?)([^\s'\"]{8,})(['\"]?)"),
            re.compile(r"(?i)(pwd\s*[:=]\s*['\"]?)([^\s'\"]{8,})(['\"]?)"),
        ],
        "token": [
            re.compile(r"(?i)(token\s*[:=]\s*['\"]?)([A-Za-z0-9_\-\.]{20,})(['\"]?)"),
            re.compile(r"(?i)(bearer\s+)([A-Za-z0-9_\-\.]{20,})"),
            re.compile(r"(?i)(jwt\s+)([A-Za-z0-9_\-\.]{20,})"),
        ],
        "email": [
            re.compile(r"([a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})"),
        ],
        "aws_key": [
            re.compile(r"(AKIA[0-9A-Z]{16})"),
        ],
        "private_key": [
            re.compile(r"(-----BEGIN (?:RSA |EC |DSA )?PRIVATE KEY-----)"),
        ],
    }
    
    def __init__(self, audit_service: AuditService | None = None) -> None:
        self._audit_service = audit_service
    
    def redact(self, text: str) -> RedactionResult:
        """Redact secrets from text."""
        redacted_text = text
        redaction_count = 0
        redaction_types = []
        
        for secret_type, patterns in self.PATTERNS.items():
            for pattern in patterns:
                matches = list(pattern.finditer(redacted_text))
                if matches:
                    redaction_count += len(matches)
                    if secret_type not in redaction_types:
                        redaction_types.append(secret_type)
                    
                    # Replace matches with redacted version
                    for match in reversed(matches):  # Reverse to maintain positions
                        start, end = match.span()
                        # Keep the prefix and suffix, redact the secret
                        if match.lastindex and match.lastindex >= 3:
                            # Pattern has prefix, secret, suffix groups
                            prefix = match.group(1)
                            suffix = match.group(3)
                            redacted_secret = f"{prefix}[REDACTED_{secret_type.upper()}]{suffix}"
                        elif match.lastindex and match.lastindex >= 2:
                            # Pattern has prefix, secret groups
                            prefix = match.group(1)
                            redacted_secret = f"{prefix}[REDACTED_{secret_type.upper()}]"
                        else:
                            # Pattern has only the secret group
                            redacted_secret = f"[REDACTED_{secret_type.upper()}]"
                        redacted_text = redacted_text[:start] + redacted_secret + redacted_text[end:]
        
        # Log redaction event if audit service is available
        if self._audit_service and redaction_count > 0:
            self._audit_service.log_event(
                event_type="llm.redaction",
                entity_type="llm",
                entity_id=new_id(),
                actor_type="system",
                actor_id="redactor",
                payload={
                    "redaction_count": redaction_count,
                    "redaction_types": redaction_types,
                    "original_length": len(text),
                    "redacted_length": len(redacted_text),
                },
                note=f"Redacted {redaction_count} secrets of types: {', '.join(redaction_types)}",
            )
        
        return RedactionResult(
            redacted_text=redacted_text,
            redaction_count=redaction_count,
            redaction_types=redaction_types,
        )
    
    def redact_dict(self, data: dict[str, Any]) -> dict[str, Any]:
        """Recursively redact secrets from a dictionary."""
        if isinstance(data, str):
            result = self.redact(data)
            return result.redacted_text
        elif isinstance(data, dict):
            return {k: self.redact_dict(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self.redact_dict(item) for item in data]
        else:
            return data