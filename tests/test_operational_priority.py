from src.services.alerts import InvestigationAlert
from src.services.prioritization import calculate_operational_priority

def alert(code: str) -> InvestigationAlert:
    return InvestigationAlert("high", code, code, "rationale", "action")

def test_score_is_explainable_and_capped_at_100():
    result = calculate_operational_priority([
        alert("SYMPTOMATIC_CONTACT"),
        alert("POST_MORTEM_EXPOSURE"),
        alert("OVERDUE_WITHOUT_OUTCOME"),
        alert("TRANSMISSION_REVIEW"),
    ], validation_issue_count=3)
    assert result.score == 100
    assert result.level == "immediate_review"
    assert result.factors
    assert all(f.rationale for f in result.factors)

def test_zero_score_is_not_a_diagnostic_statement():
    result = calculate_operational_priority([])
    assert result.score == 0
    assert result.level == "no_flag"
    assert "fator de priorização operacional" in result.interpretation
