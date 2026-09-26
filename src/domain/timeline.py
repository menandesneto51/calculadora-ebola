"""Marcos temporais epidemiológicos com proveniência."""
from dataclasses import dataclass
from datetime import date
from typing import Literal

Provenance = Literal["observed","reported","derived","estimated"]

@dataclass(frozen=True)
class TimelineEvent:
    event_id: str
    entity_id: str
    event_type: str
    event_date: date
    provenance: Provenance
    source: str
    notes: str | None = None
