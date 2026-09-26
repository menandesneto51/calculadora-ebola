"""Motor inicial de alertas operacionais da V17."""
from dataclasses import dataclass
from datetime import date

@dataclass(frozen=True)
class InvestigationAlert:
    priority: str
    code: str
    title: str
    rationale: str
    recommended_action: str

_PRIORITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}

def build_investigation_alerts(
    *,
    evolution: str | None = None,
    monitoring_end: date | None = None,
    symptomatic: bool = False,
    post_mortem_exposure: bool = False,
    has_outcome: bool = True,
    has_source_case: bool = True,
    today: date | None = None,
) -> list[InvestigationAlert]:
    reference_today = today or date.today()
    alerts: list[InvestigationAlert] = []

    if symptomatic:
        alerts.append(InvestigationAlert(
            "critical", "SYMPTOMATIC_CONTACT", "Contato sintomático",
            "Contato em investigação apresenta sintomas.",
            "Priorizar avaliação epidemiológica e aplicação do protocolo vigente."
        ))
    if post_mortem_exposure:
        alerts.append(InvestigationAlert(
            "high", "POST_MORTEM_EXPOSURE", "Exposição pós-morte",
            "Há registro de exposição durante manejo do corpo, funeral ou período pós-morte.",
            "Revisar expostos, tipo de contato e data da última exposição."
        ))
    if monitoring_end:
        delta = (monitoring_end - reference_today).days
        if delta == 0:
            alerts.append(InvestigationAlert(
                "medium", "MONITORING_ENDS_TODAY", "Monitoramento termina hoje",
                "O período operacional de acompanhamento termina na data de referência.",
                "Confirmar ausência de sintomas e registrar desfecho antes do encerramento."
            ))
        elif delta == 1:
            alerts.append(InvestigationAlert(
                "low", "MONITORING_ENDS_TOMORROW", "Monitoramento termina amanhã",
                "O contato está próximo do término do acompanhamento.",
                "Programar verificação final e documentação do desfecho."
            ))
        elif delta < 0 and not has_outcome:
            alerts.append(InvestigationAlert(
                "high", "OVERDUE_WITHOUT_OUTCOME", "Seguimento vencido sem desfecho",
                "O período de acompanhamento terminou e não há desfecho registrado.",
                "Realizar busca/checagem de encerramento e qualificar o registro."
            ))
    if not has_source_case:
        alerts.append(InvestigationAlert(
            "medium", "MISSING_SOURCE_CASE", "Contato sem caso-origem",
            "O registro não possui vínculo com caso-origem.",
            "Revisar investigação e vincular o contato quando houver evidência."
        ))
    if evolution in {"Confirmado", "Óbito"}:
        alerts.append(InvestigationAlert(
            "high", "TRANSMISSION_REVIEW", "Revisar cadeia de transmissão",
            "A evolução registrada requer revisão dos vínculos epidemiológicos e contatos relacionados.",
            "Recalcular gerações, exposições e contatos prioritários."
        ))
    return sorted(alerts, key=lambda item: _PRIORITY_ORDER[item.priority])
