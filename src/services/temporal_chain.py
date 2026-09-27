"""Análise temporal de vínculos sem afirmar transmissão confirmada."""
from dataclasses import dataclass
from datetime import date
from typing import Literal, Any

from src.domain.exposure import Exposure
from src.epidemiology.parameters import EpidemiologyParameters

Compatibility=Literal["compatible","incompatible","indeterminate"]

@dataclass(frozen=True)
class TemporalLink:
    source_id:str
    target_id:str
    compatibility:Compatibility
    generation:int|None
    serial_interval_days:int|None
    rationale:str
    infectiousness_compatibility:Compatibility="indeterminate"
    incubation_compatibility:Compatibility="indeterminate"
    exposure_start:date|None=None
    exposure_end:date|None=None
    incubation_min_days:int|None=None
    incubation_max_days:int|None=None

def analyze_temporal_chain(
    rows:list[dict[str,Any]],
    exposures:list[Exposure]|None=None,
    params:EpidemiologyParameters|None=None,
)->list[TemporalLink]:
    p=params or EpidemiologyParameters()
    p.validate()
    structured=exposures or []
    by_id={_text(r.get("identificador")):r for r in rows if _text(r.get("identificador"))}
    generations=_generations(by_id)
    links=[]
    for target,row in by_id.items():
        source=_text(row.get("caso_origem"))
        if not source or source=="Caso índice": continue
        if source not in by_id:
            links.append(TemporalLink(source,target,"indeterminate",None,None,"Caso-origem não disponível no conjunto analisado."))
            continue

        source_onset=_date(by_id[source].get("data_inicio_sintomas"))
        target_onset=_date(row.get("data_inicio_sintomas"))
        relevant=[x for x in structured if x.contact_id==target and x.source_case_id==source]
        if relevant:
            exposure_start=min(x.start_date for x in relevant)
            exposure_end=max(x.end_date for x in relevant)
        else:
            legacy=_date(row.get("data_ultimo_contato"))
            exposure_start=legacy
            exposure_end=legacy

        serial=(target_onset-source_onset).days if source_onset and target_onset else None
        infectiousness=_infectiousness_compatibility(source_onset,exposure_start,exposure_end)
        incubation,inc_min,inc_max=_incubation_compatibility(target_onset,exposure_start,exposure_end,p)
        overall=_overall(infectiousness,incubation)
        rationale=_rationale(infectiousness,incubation,bool(relevant))
        links.append(TemporalLink(
            source,target,overall,generations.get(target),serial,rationale,
            infectiousness,incubation,exposure_start,exposure_end,inc_min,inc_max,
        ))
    return links

def _infectiousness_compatibility(source_onset:date|None,start:date|None,end:date|None)->Compatibility:
    if not source_onset or not start or not end:return "indeterminate"
    if end < source_onset:return "incompatible"
    return "compatible"

def _incubation_compatibility(
    target_onset:date|None,start:date|None,end:date|None,p:EpidemiologyParameters
)->tuple[Compatibility,int|None,int|None]:
    if not target_onset or not start or not end:return "indeterminate",None,None
    min_days=(target_onset-end).days
    max_days=(target_onset-start).days
    if max_days < p.incubation_min_days or min_days > p.incubation_max_days:
        return "incompatible",min_days,max_days
    return "compatible",min_days,max_days

def _overall(infectiousness:Compatibility,incubation:Compatibility)->Compatibility:
    if "incompatible" in {infectiousness,incubation}:return "incompatible"
    if infectiousness=="compatible" and incubation=="compatible":return "compatible"
    return "indeterminate"

def _rationale(infectiousness:Compatibility,incubation:Compatibility,structured:bool)->str:
    origin="histórico estruturado de exposições" if structured else "campo legado de última exposição"
    return (
        f"Fonte temporal: {origin}. Compatibilidade com início de sintomas do caso-origem: "
        f"{infectiousness}. Compatibilidade com janela protocolar de incubação: {incubation}. "
        "Compatibilidade temporal não confirma transmissão."
    )

def _generations(by_id:dict[str,dict[str,Any]])->dict[str,int|None]:
    memo={}
    def resolve(node,path):
        if node in memo:return memo[node]
        if node in path:return None
        source=_text(by_id[node].get("caso_origem"))
        if not source or source=="Caso índice":
            memo[node]=1; return 1
        if source not in by_id:
            memo[node]=None; return None
        parent=resolve(source,path|{node})
        memo[node]=parent+1 if parent is not None else None
        return memo[node]
    for node in by_id: resolve(node,set())
    return memo

def _text(v:Any)->str:
    if v is None:return ""
    try:
        if v!=v:return ""
    except Exception:pass
    return str(v).strip()

def _date(v:Any)->date|None:
    if isinstance(v,date):return v
    if v is None:return None
    try:
        from pandas import to_datetime
        p=to_datetime(v,errors="coerce")
        if p!=p:return None
        return p.date()
    except Exception:return None
