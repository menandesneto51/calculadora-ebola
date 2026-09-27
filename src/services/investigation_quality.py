"""Qualidade estrutural da investigação e da cadeia de contatos."""
from dataclasses import dataclass
from datetime import date
from typing import Any

from src.domain.exposure import Exposure

@dataclass(frozen=True)
class QualityIssue:
    severity: str
    code: str
    entity_id: str
    description: str
    recommended_action: str

@dataclass(frozen=True)
class InvestigationQuality:
    score: int
    total_records: int
    complete_records: int
    issues: tuple[QualityIssue, ...]

_REQUIRED = ("identificador","data_ultimo_contato","tipo_contato","evolucao")

def assess_investigation_quality(rows:list[dict[str,Any]], exposures:list[Exposure]|None=None) -> InvestigationQuality:
    issues:list[QualityIssue]=[]
    ids=[_text(r.get("identificador")) for r in rows]
    valid_ids={x for x in ids if x}
    seen:set[str]=set()
    complete=0

    for r in rows:
        cid=_text(r.get("identificador"))
        if cid and cid in seen:
            issues.append(QualityIssue("error","DUPLICATE_CONTACT",cid,"Identificador duplicado.","Consolidar ou corrigir o identificador antes da análise."))
        if cid: seen.add(cid)

        missing=[f for f in _REQUIRED if not _present(r.get(f))]
        if not missing:
            complete+=1
        else:
            issues.append(QualityIssue("warning","MISSING_REQUIRED_FIELDS",cid or "(sem id)",f"Campos essenciais ausentes: {', '.join(missing)}.","Completar os campos essenciais da investigação."))

        source=_text(r.get("caso_origem")) or "Caso índice"
        if cid and source==cid:
            issues.append(QualityIssue("error","SELF_LINK",cid,"Contato vinculado a si próprio como caso-origem.","Corrigir o caso-origem."))
        elif source!="Caso índice" and source not in valid_ids:
            issues.append(QualityIssue("warning","ORPHAN_SOURCE",cid or "(sem id)",f"Caso-origem '{source}' não localizado.","Cadastrar/localizar o caso-origem ou corrigir o vínculo."))

        exposure=_date(r.get("data_ultimo_contato"))
        onset=_date(r.get("data_inicio_sintomas"))
        if exposure and onset and onset < exposure:
            issues.append(QualityIssue("error","ONSET_BEFORE_EXPOSURE",cid or "(sem id)","Início dos sintomas anterior à exposição registrada.","Revisar datas e vínculo epidemiológico."))

    graph={_text(r.get("identificador")):(_text(r.get("caso_origem")) or "Caso índice") for r in rows if _text(r.get("identificador"))}
    for node in graph:
        if _has_cycle(node,graph):
            issues.append(QualityIssue("error","TRANSMISSION_CYCLE",node,"Ciclo detectado na cadeia de casos-origem.","Revisar vínculos; uma cadeia temporal não deve formar ciclo."))
    structured=exposures or []
    exposure_ids:set[str]=set()
    row_by_id={_text(r.get("identificador")):r for r in rows if _text(r.get("identificador"))}
    for exposure in structured:
        eid=exposure.exposure_id
        if eid in exposure_ids:
            issues.append(QualityIssue("error","DUPLICATE_EXPOSURE",eid,"Identificador de exposição duplicado.","Corrigir ou consolidar a exposição antes da análise."))
        exposure_ids.add(eid)

        if exposure.contact_id not in valid_ids:
            issues.append(QualityIssue("error","EXPOSURE_UNKNOWN_CONTACT",eid,f"Contato '{exposure.contact_id}' da exposição não localizado.","Vincular a exposição a um contato existente ou corrigir o identificador."))
        if exposure.source_case_id not in valid_ids and exposure.source_case_id!="Caso índice":
            issues.append(QualityIssue("warning","EXPOSURE_UNKNOWN_SOURCE",eid,f"Caso-origem '{exposure.source_case_id}' da exposição não localizado.","Cadastrar/localizar o caso-origem ou revisar o vínculo."))

        target=row_by_id.get(exposure.contact_id)
        if target:
            onset=_date(target.get("data_inicio_sintomas"))
            if onset and onset < exposure.start_date:
                issues.append(QualityIssue("error","ONSET_BEFORE_STRUCTURED_EXPOSURE",eid,"Início dos sintomas do contato é anterior ao início da exposição estruturada.","Revisar datas e vínculo epidemiológico."))
            legacy=_date(target.get("data_ultimo_contato"))
            if legacy and legacy != exposure.end_date:
                issues.append(QualityIssue("warning","LEGACY_EXPOSURE_MISMATCH",eid,f"Campo legado de última exposição ({legacy.isoformat()}) difere do fim da exposição estruturada ({exposure.end_date.isoformat()}).","Confirmar o histórico; a V17 usa o histórico estruturado como fonte preferencial."))

        source_row=row_by_id.get(exposure.source_case_id)
        if source_row:
            source_onset=_date(source_row.get("data_inicio_sintomas"))
            if source_onset and exposure.end_date < source_onset:
                issues.append(QualityIssue("warning","EXPOSURE_BEFORE_SOURCE_ONSET",eid,"Exposição terminou antes do início de sintomas registrado do caso-origem.","Revisar vínculo e datas; este achado não confirma nem exclui transmissão isoladamente."))

    issues=_dedupe(issues)

    penalty=sum(20 if x.severity=="error" else 8 for x in issues)
    score=max(0,100-min(penalty,100))
    return InvestigationQuality(score,len(rows),complete,tuple(issues))

def _has_cycle(start:str,graph:dict[str,str])->bool:
    visited:set[str]=set()
    node=start
    while node in graph:
        if node in visited: return True
        visited.add(node)
        node=graph[node]
    return False

def _dedupe(items:list[QualityIssue])->list[QualityIssue]:
    out=[]; keys=set()
    for x in items:
        key=(x.code,x.entity_id)
        if key not in keys:
            keys.add(key); out.append(x)
    return out

def _text(value:Any)->str:
    if value is None: return ""
    try:
        if value != value: return ""
    except Exception: pass
    return str(value).strip()

def _present(value:Any)->bool:
    return bool(_text(value))

def _date(value:Any)->date|None:
    if isinstance(value,date): return value
    if value is None: return None
    try:
        from pandas import to_datetime
        parsed=to_datetime(value,errors="coerce")
        if parsed != parsed: return None
        return parsed.date()
    except Exception:
        return None
