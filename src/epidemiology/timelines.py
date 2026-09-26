"""Cálculos temporais puros e auditáveis para a V17."""
from datetime import date, timedelta
from .parameters import EpidemiologyParameters

def symptom_window_from_exposure(last_exposure: date, params: EpidemiologyParameters | None = None) -> tuple[date, date]:
    p = params or EpidemiologyParameters()
    p.validate()
    return (
        last_exposure + timedelta(days=p.incubation_min_days),
        last_exposure + timedelta(days=p.incubation_max_days),
    )

def exposure_window_from_onset(symptom_onset: date, params: EpidemiologyParameters | None = None) -> tuple[date, date]:
    p = params or EpidemiologyParameters()
    p.validate()
    return (
        symptom_onset - timedelta(days=p.incubation_max_days),
        symptom_onset - timedelta(days=p.incubation_min_days),
    )

def contact_followup_end(last_exposure: date, params: EpidemiologyParameters | None = None) -> date:
    p = params or EpidemiologyParameters()
    p.validate()
    return last_exposure + timedelta(days=p.contact_followup_days)
