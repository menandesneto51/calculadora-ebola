"""Agregação executiva dos motores V17, sem duplicar regras epidemiológicas."""
from dataclasses import dataclass
from typing import Any
from src.domain.exposure import Exposure
from src.services.investigation_quality import assess_investigation_quality
from src.services.temporal_chain import analyze_temporal_chain

@dataclass(frozen=True)
class CommandCenterSummary:
    contacts:int
    exposures:int
    quality_score:int
    quality_issues:int
    temporal_links:int
    incompatible_links:int
    indeterminate_links:int
    symptomatic_or_suspected:int
    confirmed:int
    deaths:int
    monitoring_due:int
    monitoring_overdue:int

def build_command_center(rows:list[dict[str,Any]],exposures:list[Exposure],today)->CommandCenterSummary:
    quality=assess_investigation_quality(rows)
    links=analyze_temporal_chain(rows)
    due=overdue=0
    for r in rows:
        end=_date(r.get("data_fim_monitoramento"))
        if end is None:
            last=_date(r.get("data_ultimo_contato"))
            end=last.fromordinal(last.toordinal()+21) if last else None
        evolution=_text(r.get("evolucao")).lower()
        closed=("encerr" in evolution or "descart" in evolution)
        if end and not closed:
            if end < today: overdue+=1
            elif end == today: due+=1
    evol=[_text(r.get("evolucao")).lower() for r in rows]
    return CommandCenterSummary(
        contacts=len(rows),exposures=len(exposures),quality_score=quality.score,quality_issues=len(quality.issues),
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
    from datetime import date
    if isinstance(v,date):return v
    if v is None:return None
    try:
        from pandas import to_datetime
        p=to_datetime(v,errors="coerce")
        if p!=p:return None
        return p.date()
    except Exception:return None
