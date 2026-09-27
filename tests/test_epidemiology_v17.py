from datetime import date
from src.epidemiology.parameters import EpidemiologyParameters
from src.epidemiology.timelines import contact_followup_end, exposure_window_from_onset, symptom_window_from_exposure
from src.data.validation import validate_case_timeline

def test_official_default_incubation_window_is_2_to_21_days():
    p = EpidemiologyParameters()
    assert (p.incubation_min_days, p.incubation_max_days) == (2, 21)

def test_symptom_window_boundaries():
    assert symptom_window_from_exposure(date(2026, 1, 1)) == (date(2026, 1, 3), date(2026, 1, 22))

def test_exposure_window_boundaries():
    assert exposure_window_from_onset(date(2026, 1, 22)) == (date(2026, 1, 1), date(2026, 1, 20))

def test_contact_followup_is_21_days_after_last_exposure():
    assert contact_followup_end(date(2026, 1, 1)) == date(2026, 1, 22)

def test_impossible_timeline_is_flagged():
    issues = validate_case_timeline(exposure_date=date(2026, 1, 10), symptom_onset=date(2026, 1, 9), today=date(2026, 2, 1))
    assert any(i.code == "ONSET_BEFORE_EXPOSURE" for i in issues)
