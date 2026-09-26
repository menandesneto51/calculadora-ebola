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
