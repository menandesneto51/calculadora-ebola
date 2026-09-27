"""Validações temporais V17 sem dependência da interface."""
from dataclasses import dataclass
from datetime import date

@dataclass(frozen=True)
class ValidationIssue:
    severity: str
    code: str
    description: str
    recommended_action: str

def validate_case_timeline(
    *,
    exposure_date: date | None = None,
    symptom_onset: date | None = None,
    detection_date: date | None = None,
    death_date: date | None = None,
    today: date | None = None,
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    reference_today = today or date.today()

    if exposure_date and exposure_date > reference_today:
        issues.append(ValidationIssue("error","FUTURE_EXPOSURE","Data de exposição está no futuro.","Verificar/corrigir a data de exposição."))
    if exposure_date and symptom_onset and symptom_onset < exposure_date:
        issues.append(ValidationIssue("error","ONSET_BEFORE_EXPOSURE","Início dos sintomas anterior à exposição informada.","Revisar vínculo epidemiológico e datas."))
    if symptom_onset and death_date and death_date < symptom_onset:
        issues.append(ValidationIssue("error","DEATH_BEFORE_ONSET","Óbito anterior ao início dos sintomas.","Revisar datas clínicas."))
    if detection_date and death_date and detection_date > death_date:
        issues.append(ValidationIssue("warning","DETECTION_AFTER_DEATH","Detecção registrada após o óbito.","Confirmar se se trata de detecção/investigação retrospectiva."))
    return issues
