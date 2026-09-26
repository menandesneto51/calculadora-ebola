import json
from src.domain.outbreak import OutbreakEvent
from src.services.event_registry import build_event_snapshot, create_audit_entry, snapshot_to_json

def test_snapshot_is_versioned_and_has_checksum():
    event = OutbreakEvent("EVT-2026-001", "Investigação teste", "Mato Grosso")
    snapshot = build_event_snapshot(event, {"total_contacts": 3}, snapshot_version=2)
    assert snapshot.event_id == "EVT-2026-001"
    assert snapshot.snapshot_version == 2
    assert len(snapshot.checksum_sha256) == 64

def test_snapshot_json_contains_metadata():
    event = OutbreakEvent("EVT-001", "Teste", "MT")
    doc = json.loads(snapshot_to_json(build_event_snapshot(event, {"x": 1})))
    assert doc["metadata"]["event_id"] == "EVT-001"
    assert doc["metadata"]["protocol_version"] == "2026-09"
    assert doc["payload"]["x"] == 1

def test_audit_entry_keeps_event_scope():
    event = OutbreakEvent("EVT-001", "Teste", "MT")
    entry = create_audit_entry(event, "snapshot_created", "event", event.event_id)
    assert entry.event_id == event.event_id
    assert entry.action == "snapshot_created"
