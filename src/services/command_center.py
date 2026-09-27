"""Agregação executiva e gate de promoção dos motores V17."""
from dataclasses import dataclass
from datetime import date
from typing import Any

from src.domain.exposure import Exposure
from src.epidemiology.parameters import EpidemiologyParameters
from src.epidemiology.timelines import contact_followup_end
from src.services.exposure_history import effective_last_exposure
from src.services.investigation_quality import assess_investigation_quality
from src.services.temporal_chain import analyze_temporal_chain

BLOCKING_QUALITY_CODES=frozenset({
    "DUPLICATE_CONTACT","SELF_LINK","TRANSMISSION_CYCLE",
    "DUPLICATE_EXPOSURE","EXPOSURE_UNKNOWN_CONTACT","ONSET_BEFORE_STRUCTURED_EXPOSURE",
})

@dataclass(frozen=True)
class CommandCenterSummary:
    contacts:int
    exposures:int
    quality_score:int
    quality_issues:int
    blocking_issues:int
    promotion_allowed:bool
    blocking_codes:tuple[str,...]
    temporal_links:int
    incompatible_links:int
    indeterminate_links:int
    symptomatic_or_suspected:int
    confirmed:int
    deaths:int
    monitoring_due:int
    monitoring_overdue:int

def build_command_center(
    rows:list[dict[str,Any]],exposures:list[Exposure],today:date,
    params:EpidemiologyParameters|None=None,
)->CommandCenterSummary:
    p=params or EpidemiologyParameters()
    p.validate()
    quality=assess_investigation_quality(rows,exposures)
    links=analyze_temporal_chain(rows,exposures,p)
    blockers=tuple(x for x in quality.issues if x.severity=="error" and x.code in BLOCKING_QUALITY_CODES)
    due=overdue=0
    for r in rows:
        end=_date(r.get("data_fim_monitoramento"))
        if end is None:
            cid=_text(r.get("identificador"))
            last=effective_last_exposure(cid,exposures,_date(r.get("data_ultimo_contato")))
            end=contact_followup_end(last,p) if last else None
        evolution=_text(r.get("evolucao")).lower()
        closed=("encerr" in evolution or "descart" in evolution)
        if end and not closed:
            if end < today: overdue+=1
            elif end == today: due+=1
    evol=[_text(r.get("evolucao")).lower() for r in rows]
    codes=tuple(sorted({x.code for x in blockers}))
    return CommandCenterSummary(
        contacts=len(rows),exposures=len(exposures),quality_score=quality.score,quality_issues=len(quality.issues),
        blocking_issues=len(blockers),promotion_allowed=not blockers,blocking_codes=codes,
        temporal_links=len(links),incompatible_links=sum(x.compatibility=="incompatible" for x in links),
        indeterminate_links=sum(x.compatibility=="indeterminate" for x in links),
        symptomatic_or_suspected=sum(("sintom" in x or "suspeit" in x) for x in evol),
        confirmed=sum("confirm" in x for x in evol),deaths=sum(("óbito" in x or "obito" in x) for x in evol),
        monitoring_due=due,monitoring_overdue=overdue,
    )

def _text(v):
    if v is None:return ""
    try:
        if v!=v:return ""
    except Exception:pass
    return str(v).strip()

def _date(v):
    if isinstance(v,date):return v
    if v is None:return None
    try:
        from pandas import to_datetime
        p=to_datetime(v,errors="coerce")
        if p!=p:return None
        return p.date()
    except Exception:return None
