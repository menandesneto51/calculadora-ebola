"""Parâmetros epidemiológicos V17.

Regras oficiais e hipóteses operacionais devem permanecer semanticamente separadas.
"""
from dataclasses import dataclass

@dataclass(frozen=True)
class EpidemiologyParameters:
    incubation_min_days: int = 2
    incubation_max_days: int = 21
    contact_followup_days: int = 21
    infectiousness_begins_at: str = "symptom_onset"
    protocol_version: str = "2026-09"

    def validate(self) -> None:
        if self.incubation_min_days < 0:
            raise ValueError("incubation_min_days deve ser >= 0")
        if self.incubation_max_days < self.incubation_min_days:
            raise ValueError("incubation_max_days deve ser >= incubation_min_days")
        if self.contact_followup_days <= 0:
            raise ValueError("contact_followup_days deve ser > 0")
