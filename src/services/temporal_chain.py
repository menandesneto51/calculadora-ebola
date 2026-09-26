"""Análise temporal de vínculos sem afirmar transmissão confirmada."""
from dataclasses import dataclass
from datetime import date
from typing import Literal, Any

Compatibility=Literal["compatible","incompatible","indeterminate"]

@dataclass(frozen=True)
class TemporalLink:
    source_id:str
    target_id:str
    compatibility:Compatibility
    generation:int|None
    serial_interval_days:int|None
    rationale:str

def analyze_temporal_chain(rows:list[dict[str,Any]])->list[TemporalLink]:
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
        exposure=_date(row.get("data_ultimo_contato"))
        serial=(target_onset-source_onset).days if source_onset and target_onset else None
        if source_onset and exposure and exposure < source_onset:
            compatibility="incompatible"
            rationale="Exposição registrada ocorreu antes do início de sintomas do caso-origem."
        elif source_onset and exposure:
            compatibility="compatible"
            rationale="Exposição registrada ocorreu no mesmo dia ou após o início de sintomas do caso-origem."
        else:
            compatibility="indeterminate"
            rationale="Datas insuficientes para avaliar compatibilidade temporal."
        links.append(TemporalLink(source,target,compatibility,generations.get(target),serial,rationale))
    return links

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
