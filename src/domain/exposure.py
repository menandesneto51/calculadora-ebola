"""Exposição individual vinculada a contato e evento."""
from dataclasses import dataclass
from datetime import date

@dataclass(frozen=True)
class Exposure:
    exposure_id: str
    event_id: str
    contact_id: str
    source_case_id: str
    start_date: date
    end_date: date
    exposure_type: str
    location: str | None = None
    notes: str | None = None

    def validate(self) -> None:
        if not self.exposure_id.strip(): raise ValueError("exposure_id é obrigatório")
        if not self.event_id.strip(): raise ValueError("event_id é obrigatório")
        if not self.contact_id.strip(): raise ValueError("contact_id é obrigatório")
        if not self.source_case_id.strip(): raise ValueError("source_case_id é obrigatório")
        if self.end_date < self.start_date: raise ValueError("end_date não pode ser anterior a start_date")
