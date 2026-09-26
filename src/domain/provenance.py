"""Modelo de proveniência para resultados epidemiológicos."""
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Generic, Literal, TypeVar

T = TypeVar("T")
SourceType = Literal["observed", "reported", "derived", "estimated"]

@dataclass(frozen=True)
class ProvenancedValue(Generic[T]):
    value: T
    source_type: SourceType
    calculation_method: str
    protocol_version: str
    confidence: str = "high"
    generated_at: datetime | None = None

    def __post_init__(self) -> None:
        if self.generated_at is None:
            object.__setattr__(self, "generated_at", datetime.now(timezone.utc))
