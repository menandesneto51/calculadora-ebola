"""Construção de timelines sem afirmar causalidade de transmissão."""
from datetime import date
from src.domain.exposure import Exposure
from src.domain.timeline import TimelineEvent

def build_contact_timeline(
    event_id:str,
    contact_id:str,
    *,
    exposures:list[Exposure],
    symptom_onset:date|None=None,
    detection_date:date|None=None,
    death_date:date|None=None,
    monitoring_end:date|None=None,
)->list[TimelineEvent]:
    events=[]
    for x in exposures:
        if x.contact_id != contact_id: continue
        events.append(TimelineEvent(event_id,contact_id,"exposure_start",x.start_date,"reported",x.exposure_id,x.exposure_type))
        if x.end_date != x.start_date:
            events.append(TimelineEvent(event_id,contact_id,"exposure_end",x.end_date,"reported",x.exposure_id,x.exposure_type))
    if symptom_onset:
        events.append(TimelineEvent(event_id,contact_id,"symptom_onset",symptom_onset,"reported","contact_record"))
    if detection_date:
        events.append(TimelineEvent(event_id,contact_id,"detection",detection_date,"reported","contact_record"))
    if death_date:
        events.append(TimelineEvent(event_id,contact_id,"death",death_date,"reported","contact_record"))
    if monitoring_end:
        events.append(TimelineEvent(event_id,contact_id,"monitoring_end",monitoring_end,"derived","protocol","last_exposure + followup"))
    return sorted(events,key=lambda x:(x.event_date,x.event_type))

def interval_days(start:date|None,end:date|None)->int|None:
    if start is None or end is None: return None
    return (end-start).days
