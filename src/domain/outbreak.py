"""Modelo agregado de evento/surto para apoio operacional V17."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Literal

EventStatus = Literal["monitoring", "active", "controlled", "closed"]

@dataclass(frozen=True)
class OutbreakEvent:
    event_id: str
    name: str
    jurisdiction: str
    status: EventStatus = "monitoring"
    protocol_version: str = "2026-09"
    municipality: str | None = None
    state: str | None = None
    country: str = "Brasil"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def validate(self) -> None:
        if not self.event_id.strip():
            raise ValueError("event_id é obrigatório")
        if not self.name.strip():
            raise ValueError("name é obrigatório")
        if not self.jurisdiction.strip():
            raise ValueError("jurisdiction é obrigatória")
