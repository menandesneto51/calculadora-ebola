"""Orquestração de inteligência epidemiológica sem dependência do Streamlit."""
from dataclasses import dataclass
from datetime import date

from src.data.validation import ValidationIssue, validate_case_timeline
from src.epidemiology.parameters import EpidemiologyParameters
from src.epidemiology.timelines import contact_followup_end, symptom_window_from_exposure
from src.domain.provenance import ProvenancedValue
from src.services.alerts import InvestigationAlert, build_investigation_alerts

@dataclass(frozen=True)
class InvestigationAssessment:
    symptom_window: ProvenancedValue[tuple[date, date]] | None
    monitoring_end: ProvenancedValue[date] | None
    validation_issues: list[ValidationIssue]
    alerts: list[InvestigationAlert]

def assess_investigation(
    *,
    last_exposure: date | None = None,
    symptom_onset: date | None = None,
    detection_date: date | None = None,
    death_date: date | None = None,
    evolution: str | None = None,
    symptomatic: bool = False,
    post_mortem_exposure: bool = False,
    has_outcome: bool = True,
    has_source_case: bool = True,
    today: date | None = None,
    params: EpidemiologyParameters | None = None,
) -> InvestigationAssessment:
    p = params or EpidemiologyParameters()
    p.validate()

    symptom_window = None
    monitoring_end = None
    if last_exposure:
        symptom_window = ProvenancedValue(
            symptom_window_from_exposure(last_exposure, p),
            "derived", "last_exposure + incubation_window",
            p.protocol_version, "high"
        )
        monitoring_end = ProvenancedValue(
            contact_followup_end(last_exposure, p),
            "derived", "last_exposure + contact_followup_days",
            p.protocol_version, "high"
        )

    issues = validate_case_timeline(
        exposure_date=last_exposure,
        symptom_onset=symptom_onset,
        detection_date=detection_date,
        death_date=death_date,
        today=today,
    )
    alerts = build_investigation_alerts(
        evolution=evolution,
        monitoring_end=monitoring_end.value if monitoring_end else None,
        symptomatic=symptomatic,
        post_mortem_exposure=post_mortem_exposure,
        has_outcome=has_outcome,
        has_source_case=has_source_case,
        today=today,
    )
    return InvestigationAssessment(symptom_window, monitoring_end, issues, alerts)
