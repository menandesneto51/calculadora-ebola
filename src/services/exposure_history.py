"""Histórico de múltiplas exposições e derivação da última exposição."""
from dataclasses import dataclass
from datetime import date
from src.domain.exposure import Exposure

@dataclass(frozen=True)
class ExposureSummary:
    contact_id: str
    exposure_count: int
    first_exposure: date | None
    last_exposure: date | None
    source_cases: tuple[str,...]
    exposure_types: tuple[str,...]

def summarize_exposures(contact_id:str, exposures:list[Exposure]) -> ExposureSummary:
    selected=[x for x in exposures if x.contact_id==contact_id]
    for x in selected: x.validate()
    if not selected:
        return ExposureSummary(contact_id,0,None,None,(),())
    return ExposureSummary(
        contact_id=contact_id,
        exposure_count=len(selected),
        first_exposure=min(x.start_date for x in selected),
        last_exposure=max(x.end_date for x in selected),
        source_cases=tuple(sorted({x.source_case_id for x in selected})),
        exposure_types=tuple(sorted({x.exposure_type for x in selected})),
    )

def effective_last_exposure(contact_id:str, exposures:list[Exposure], legacy_last_exposure:date|None=None)->date|None:
    summary=summarize_exposures(contact_id,exposures)
    return summary.last_exposure or legacy_last_exposure
