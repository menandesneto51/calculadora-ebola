from datetime import date
from pathlib import Path
from src.domain.outbreak import OutbreakEvent
from src.services.event_registry import build_event_snapshot, create_audit_entry
from src.persistence.sqlite_repository import SQLiteEventRepository

def test_repository_is_event_scoped(tmp_path: Path):
    repo=SQLiteEventRepository(tmp_path/"ebola.db"); repo.migrate()
    a=OutbreakEvent("A","Evento A","MT"); b=OutbreakEvent("B","Evento B","MT")
    repo.upsert_event(a); repo.upsert_event(b)
    repo.replace_contacts("A",[{"identificador":"C1","data_ultimo_contato":date(2026,9,1)}])
    repo.replace_contacts("B",[{"identificador":"C2"}])
    assert repo.load_contacts("A")[0]["contact_id"]=="C1"
    assert repo.load_contacts("B")[0]["contact_id"]=="C2"
    s=build_event_snapshot(a,{"total_contacts":1}); repo.save_snapshot(s)
    repo.append_audit(create_audit_entry(a,"snapshot_created","event","A"))
    assert repo.audit_for_event("A")[0]["action"]=="snapshot_created"


def test_snapshot_versions_are_sequential(tmp_path: Path):
    repo=SQLiteEventRepository(tmp_path/"ebola.db"); repo.migrate()
    event=OutbreakEvent("EVT","Evento","MT"); repo.upsert_event(event)
    assert repo.next_snapshot_version("EVT")==1
    repo.save_snapshot(build_event_snapshot(event,{"n":1},snapshot_version=1))
    assert repo.next_snapshot_version("EVT")==2
    repo.save_snapshot(build_event_snapshot(event,{"n":2},snapshot_version=2))
    history=repo.list_snapshots("EVT")
    assert [x["snapshot_version"] for x in history]==[2,1]

def test_event_status_update_preserves_identity(tmp_path: Path):
    repo=SQLiteEventRepository(tmp_path/"ebola.db"); repo.migrate()
    repo.upsert_event(OutbreakEvent("EVT","Evento","MT",status="monitoring"))
    repo.upsert_event(OutbreakEvent("EVT","Evento","MT",status="active"))
    saved=repo.get_event("EVT")
    assert saved["event_id"]=="EVT"
    assert saved["status"]=="active"


def test_multiple_exposures_persist_and_reload(tmp_path: Path):
    from src.domain.exposure import Exposure
    repo=SQLiteEventRepository(tmp_path/"ebola.db"); repo.migrate()
    event=OutbreakEvent("EVT-X","Evento X","MT"); repo.upsert_event(event)
    repo.replace_contacts("EVT-X",[{"identificador":"C1"}])
    exposures=[
        Exposure("E1","EVT-X","C1","Caso índice",date(2026,9,1),date(2026,9,1),"Contato domiciliar"),
        Exposure("E2","EVT-X","C1","Caso índice",date(2026,9,3),date(2026,9,5),"Cuidado direto"),
    ]
    repo.replace_exposures("EVT-X",exposures)
    loaded=repo.load_exposures("EVT-X")
    assert len(loaded)==2
    assert loaded[-1]["end_date"]=="2026-09-05"


def test_migration_applies_schema_v1_then_v2(tmp_path: Path):
    repo=SQLiteEventRepository(tmp_path/"ebola.db")
    repo.migrate()
    with repo.connect() as conn:
        versions=[r[0] for r in conn.execute("SELECT version FROM schema_version ORDER BY version")]
        tables={r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert versions==[1,2]
    assert "exposures" in tables

def test_migration_rejects_future_schema(tmp_path: Path):
    import pytest
    repo=SQLiteEventRepository(tmp_path/"ebola.db")
    repo.migrate()
    with repo.connect() as conn:
        conn.execute("INSERT INTO schema_version(version,applied_at) VALUES(99,'future')")
    with pytest.raises(RuntimeError):
        repo.migrate()


def test_working_state_can_be_saved_repeatedly_without_snapshot_collision(tmp_path: Path):
    event=OutbreakEvent(event_id="EV-WORK",name="Estado mutável",jurisdiction="MT")
    repo=SQLiteEventRepository(tmp_path/"ebola.db")
    repo.migrate()
    repo.upsert_event(event)
    repo.replace_contacts("EV-WORK",[{"identificador":"C1","evolucao":"Em monitoramento"}])
    repo.replace_contacts("EV-WORK",[{"identificador":"C1","evolucao":"Encerrado"}])
    assert repo.load_contacts("EV-WORK")[0]["evolution"]=="Encerrado"
    assert repo.list_snapshots("EV-WORK")==[]

def test_snapshot_version_advances_only_after_snapshot_is_persisted(tmp_path: Path):
    event=OutbreakEvent(event_id="EV-SNAP",name="Snapshot",jurisdiction="MT")
    repo=SQLiteEventRepository(tmp_path/"ebola.db")
    repo.migrate()
    repo.upsert_event(event)
    assert repo.next_snapshot_version("EV-SNAP")==1
    snapshot=build_event_snapshot(event,{"contacts":[],"exposures":[]},snapshot_version=1)
    repo.save_snapshot(snapshot)
    assert repo.next_snapshot_version("EV-SNAP")==2


def test_full_investigation_round_trip_event_contacts_exposures_snapshot(tmp_path: Path):
    from src.domain.exposure import Exposure
    repo=SQLiteEventRepository(tmp_path/"ebola.db")
    repo.migrate()
    event=OutbreakEvent("EV-ROUND","Investigação round-trip","MT",status="active")
    contacts=[
        {"identificador":"C1","caso_origem":"Caso índice","data_ultimo_contato":date(2026,9,5),
         "tipo_contato":"Contato domiciliar","evolucao":"Em monitoramento"},
    ]
    exposures=[
        Exposure("E1","EV-ROUND","C1","Caso índice",date(2026,9,1),date(2026,9,2),"Domiciliar"),
        Exposure("E2","EV-ROUND","C1","Caso índice",date(2026,9,4),date(2026,9,5),"Cuidado direto"),
    ]
    payload={
        "contacts":contacts,
        "exposures":[{
            "exposure_id":x.exposure_id,"event_id":x.event_id,"contact_id":x.contact_id,
            "source_case_id":x.source_case_id,"start_date":x.start_date.isoformat(),
            "end_date":x.end_date.isoformat(),"exposure_type":x.exposure_type,
            "location":x.location,"notes":x.notes,
        } for x in exposures],
    }
    repo.upsert_event(event)
    repo.replace_contacts(event.event_id,contacts)
    repo.replace_exposures(event.event_id,exposures)
    snapshot=build_event_snapshot(event,payload,snapshot_version=repo.next_snapshot_version(event.event_id))
    repo.save_snapshot(snapshot)

    reopened_event=repo.get_event(event.event_id)
    reopened_contacts=repo.load_contacts(event.event_id)
    reopened_exposures=repo.load_exposures(event.event_id)
    reopened_snapshots=repo.list_snapshots(event.event_id)

    assert reopened_event["status"]=="active"
    assert reopened_contacts[0]["contact_id"]=="C1"
    assert [x["exposure_id"] for x in reopened_exposures]==["E1","E2"]
    assert reopened_exposures[-1]["end_date"]=="2026-09-05"
    assert reopened_snapshots[0]["snapshot_version"]==1
    assert reopened_snapshots[0]["checksum_sha256"]==snapshot.checksum_sha256
    assert repo.next_snapshot_version(event.event_id)==2
