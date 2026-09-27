"""Priorização operacional explicável.

O score organiza trabalho de investigação. Não é diagnóstico, prognóstico,
classificação oficial de caso ou risco clínico.
"""
from dataclasses import dataclass

from src.services.alerts import InvestigationAlert

@dataclass(frozen=True)
class PriorityFactor:
    code: str
    points: int
    rationale: str

@dataclass(frozen=True)
class OperationalPriority:
    score: int
    level: str
    factors: tuple[PriorityFactor, ...]
    interpretation: str

_ALERT_POINTS = {
    "SYMPTOMATIC_CONTACT": 40,
    "POST_MORTEM_EXPOSURE": 25,
    "OVERDUE_WITHOUT_OUTCOME": 25,
    "TRANSMISSION_REVIEW": 20,
    "MISSING_SOURCE_CASE": 15,
    "MONITORING_ENDS_TODAY": 10,
    "MONITORING_ENDS_TOMORROW": 5,
}

def calculate_operational_priority(
    alerts: list[InvestigationAlert],
    *,
    validation_issue_count: int = 0,
) -> OperationalPriority:
    factors: list[PriorityFactor] = []
    for alert in alerts:
        points = _ALERT_POINTS.get(alert.code, 0)
        if points:
            factors.append(PriorityFactor(alert.code, points, alert.rationale))

    if validation_issue_count:
        points = min(validation_issue_count * 10, 30)
        factors.append(PriorityFactor(
            "DATA_QUALITY_ISSUES",
            points,
            f"{validation_issue_count} inconsistência(s) de qualidade/cronologia requer(em) revisão.",
        ))

    score = min(sum(f.points for f in factors), 100)
    if score >= 60:
        level = "immediate_review"
        interpretation = "Revisão operacional imediata recomendada."
    elif score >= 30:
        level = "priority_review"
        interpretation = "Revisão operacional prioritária recomendada."
    elif score > 0:
        level = "routine_followup"
        interpretation = "Manter acompanhamento e resolver pendências identificadas."
    else:
        level = "no_flag"
        interpretation = "Nenhum fator de priorização operacional identificado."

    return OperationalPriority(score, level, tuple(factors), interpretation)
