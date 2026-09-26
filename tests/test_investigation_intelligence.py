from datetime import date, datetime

from src.domain.provenance import ProvenancedValue
from src.services.alerts import build_investigation_alerts
from src.services.investigation import assess_investigation

def test_provenance_marks_derived_result():
    value = ProvenancedValue(21, "derived", "test", "2026-09")
    assert value.source_type == "derived"
    assert isinstance(value.generated_at, datetime)

def test_symptomatic_contact_is_critical_and_first():
    alerts = build_investigation_alerts(
        symptomatic=True,
        post_mortem_exposure=True,
        today=date(2026, 9, 26),
    )
    assert alerts[0].code == "SYMPTOMATIC_CONTACT"
    assert alerts[0].priority == "critical"

def test_overdue_contact_without_outcome_is_high_priority():
    alerts = build_investigation_alerts(
        monitoring_end=date(2026, 9, 25),
        has_outcome=False,
        today=date(2026, 9, 26),
    )
    assert any(a.code == "OVERDUE_WITHOUT_OUTCOME" for a in alerts)

def test_assessment_generates_provenanced_windows_and_alerts():
    assessment = assess_investigation(
        last_exposure=date(2026, 9, 5),
        symptomatic=True,
        today=date(2026, 9, 26),
    )
    assert assessment.monitoring_end is not None
    assert assessment.monitoring_end.value == date(2026, 9, 26)
    assert assessment.monitoring_end.source_type == "derived"
    assert assessment.symptom_window is not None
    assert any(a.code == "SYMPTOMATIC_CONTACT" for a in assessment.alerts)
    assert any(a.code == "MONITORING_ENDS_TODAY" for a in assessment.alerts)
