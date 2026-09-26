"""Repository SQLite local; a interface deve persistir somente por ação explícita."""
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
from typing import Any

from src.domain.audit import AuditEntry
from src.domain.outbreak import OutbreakEvent
from src.services.event_registry import EventSnapshot
from .schema import MIGRATIONS

class SQLiteEventRepository:
    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path)

    def connect(self) -> sqlite3.Connection:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def migrate(self) -> None:
        with self.connect() as conn:
            conn.execute("CREATE TABLE IF NOT EXISTS schema_version (version INTEGER NOT NULL PRIMARY KEY, applied_at TEXT NOT NULL)")
            applied = {row[0] for row in conn.execute("SELECT version FROM schema_version")}
            for version in sorted(MIGRATIONS):
                if version not in applied:
                    conn.executescript(MIGRATIONS[version])
                    conn.execute("INSERT INTO schema_version VALUES (?,?)",(version,datetime.now(timezone.utc).isoformat()))

    def upsert_event(self, event: OutbreakEvent) -> None:
        event.validate()
        now=datetime.now(timezone.utc).isoformat()
        with self.connect() as conn:
            conn.execute("""INSERT INTO events VALUES(?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(event_id) DO UPDATE SET name=excluded.name,jurisdiction=excluded.jurisdiction,
            status=excluded.status,protocol_version=excluded.protocol_version,municipality=excluded.municipality,
            state=excluded.state,country=excluded.country,updated_at=excluded.updated_at""",
            (event.event_id,event.name,event.jurisdiction,event.status,event.protocol_version,event.municipality,
             event.state,event.country,event.created_at.isoformat(),now))

    def list_events(self) -> list[dict[str,Any]]:
        with self.connect() as conn:
            return [dict(r) for r in conn.execute("SELECT * FROM events ORDER BY updated_at DESC")]

    def get_event(self,event_id:str) -> dict[str,Any]|None:
        with self.connect() as conn:
            row=conn.execute("SELECT * FROM events WHERE event_id=?",(event_id,)).fetchone()
            return dict(row) if row else None

    def replace_contacts(self,event_id:str,contacts:list[dict[str,Any]]) -> None:
        now=datetime.now(timezone.utc).isoformat()
        with self.connect() as conn:
            conn.execute("DELETE FROM contacts WHERE event_id=?",(event_id,))
            for x in contacts:
                cid=str(x.get("identificador") or x.get("contact_id") or "").strip()
                if not cid: continue
                conn.execute("""INSERT INTO contacts VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (event_id,cid,x.get("caso_origem"),_iso(x.get("data_ultimo_contato")),x.get("tipo_contato"),
                 x.get("municipio"),x.get("risco"),x.get("evolucao"),_iso(x.get("data_inicio_sintomas")),
                 _iso(x.get("data_fim_transmissibilidade")),_iso(x.get("data_ultima_avaliacao")),
                 x.get("observacao"),now))

    def load_contacts(self,event_id:str) -> list[dict[str,Any]]:
        with self.connect() as conn:
            return [dict(r) for r in conn.execute("SELECT * FROM contacts WHERE event_id=? ORDER BY contact_id",(event_id,))]

    def save_snapshot(self,s:EventSnapshot) -> None:
        with self.connect() as conn:
            conn.execute("INSERT INTO snapshots VALUES(?,?,?,?,?,?)",
            (s.event_id,s.snapshot_version,s.protocol_version,s.generated_at.isoformat(),s.checksum_sha256,
             json.dumps(s.payload,ensure_ascii=False,default=str)))

    def append_audit(self,e:AuditEntry) -> None:
        with self.connect() as conn:
            conn.execute("""INSERT INTO audit_log(event_id,action,entity_type,entity_id,actor,details_json,occurred_at)
            VALUES(?,?,?,?,?,?,?)""",(e.event_id,e.action,e.entity_type,e.entity_id,e.actor,
            json.dumps(e.details,ensure_ascii=False,default=str),e.occurred_at.isoformat()))

    def audit_for_event(self,event_id:str) -> list[dict[str,Any]]:
        with self.connect() as conn:
            return [dict(r) for r in conn.execute("SELECT * FROM audit_log WHERE event_id=? ORDER BY occurred_at DESC,id DESC",(event_id,))]

    def list_snapshots(self,event_id:str) -> list[dict[str,Any]]:
        with self.connect() as conn:
            return [dict(r) for r in conn.execute(
                "SELECT event_id,snapshot_version,protocol_version,generated_at,checksum_sha256 "
                "FROM snapshots WHERE event_id=? ORDER BY snapshot_version DESC",(event_id,)
            )]

    def next_snapshot_version(self,event_id:str) -> int:
        with self.connect() as conn:
            row=conn.execute("SELECT MAX(snapshot_version) AS v FROM snapshots WHERE event_id=?",(event_id,)).fetchone()
            return int(row["v"] or 0)+1

def _iso(value:Any)->str|None:
    if value is None: return None
    if hasattr(value,"isoformat"): return value.isoformat()
    value=str(value).strip()
    return value or None
