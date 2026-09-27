from datetime import date
from src.domain.exposure import Exposure
from src.services.timeline_builder import build_contact_timeline, interval_days

def test_timeline_orders_reported_and_derived_events():
    xs=[Exposure("E1","EVT","C1","INDEX",date(2026,9,1),date(2026,9,3),"Domiciliar")]
    timeline=build_contact_timeline("EVT","C1",exposures=xs,symptom_onset=date(2026,9,10),monitoring_end=date(2026,9,24))
    assert [x.event_type for x in timeline]==["exposure_start","exposure_end","symptom_onset","monitoring_end"]
    assert timeline[-1].provenance=="derived"

def test_interval_only_when_dates_exist():
    assert interval_days(date(2026,9,1),date(2026,9,10))==9
    assert interval_days(None,date(2026,9,10)) is None
