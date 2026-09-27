"""Trilha de auditoria independente do mecanismo de persistência."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

@dataclass(frozen=True)
class AuditEntry:
    event_id: str
    action: str
    entity_type: str
    entity_id: str
    actor: str = "local-user"
    details: dict[str, Any] = field(default_factory=dict)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
