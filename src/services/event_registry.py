"""Serialização e snapshots de eventos V17.

Não persiste dados pessoais automaticamente. O backend poderá ser substituído
por SQLite/PostgreSQL/API institucional sem alterar o contrato do domínio.
"""
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
from typing import Any

from src.domain.audit import AuditEntry
from src.domain.outbreak import OutbreakEvent

@dataclass(frozen=True)
class EventSnapshot:
    event_id: str
    snapshot_version: int
    protocol_version: str
    generated_at: datetime
    payload: dict[str, Any]
    checksum_sha256: str

def event_to_dict(event: OutbreakEvent) -> dict[str, Any]:
    event.validate()
    data = asdict(event)
    data["created_at"] = event.created_at.isoformat()
    return data

def build_event_snapshot(
    event: OutbreakEvent,
    payload: dict[str, Any],
    *,
    snapshot_version: int = 1,
) -> EventSnapshot:
    event.validate()
    if snapshot_version < 1:
        raise ValueError("snapshot_version deve ser >= 1")
    envelope = {
        "event": event_to_dict(event),
        "payload": payload,
        "snapshot_version": snapshot_version,
    }
    canonical = json.dumps(envelope, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")
    checksum = hashlib.sha256(canonical).hexdigest()
    return EventSnapshot(
        event_id=event.event_id,
        snapshot_version=snapshot_version,
        protocol_version=event.protocol_version,
        generated_at=datetime.now(timezone.utc),
        payload=envelope,
        checksum_sha256=checksum,
    )

def snapshot_to_json(snapshot: EventSnapshot) -> str:
    document = {
        **snapshot.payload,
        "metadata": {
            "event_id": snapshot.event_id,
            "protocol_version": snapshot.protocol_version,
            "snapshot_version": snapshot.snapshot_version,
            "generated_at": snapshot.generated_at.isoformat(),
            "checksum_sha256": snapshot.checksum_sha256,
        },
    }
    return json.dumps(document, ensure_ascii=False, indent=2, default=str)

def create_audit_entry(
    event: OutbreakEvent,
    action: str,
    entity_type: str,
    entity_id: str,
    *,
    actor: str = "local-user",
    details: dict[str, Any] | None = None,
) -> AuditEntry:
    event.validate()
    return AuditEntry(
        event_id=event.event_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        actor=actor,
        details=details or {},
    )
