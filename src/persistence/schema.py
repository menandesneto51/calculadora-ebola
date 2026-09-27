"""Schema SQLite V17 para desenvolvimento local controlado."""
SCHEMA_VERSION = 2

MIGRATIONS = {
    1: """
    PRAGMA foreign_keys = ON;
    CREATE TABLE IF NOT EXISTS schema_version (
        version INTEGER NOT NULL PRIMARY KEY,
        applied_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS events (
        event_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        jurisdiction TEXT NOT NULL,
        status TEXT NOT NULL,
        protocol_version TEXT NOT NULL,
        municipality TEXT,
        state TEXT,
        country TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS contacts (
        event_id TEXT NOT NULL,
        contact_id TEXT NOT NULL,
        source_case_id TEXT,
        exposure_date TEXT,
        exposure_type TEXT,
        municipality TEXT,
        risk TEXT,
        evolution TEXT,
        symptom_onset_date TEXT,
        transmission_end_date TEXT,
        last_assessment_date TEXT,
        observation TEXT,
        updated_at TEXT NOT NULL,
        PRIMARY KEY (event_id, contact_id),
        FOREIGN KEY (event_id) REFERENCES events(event_id) ON DELETE CASCADE
    );
    CREATE TABLE IF NOT EXISTS snapshots (
        event_id TEXT NOT NULL,
        snapshot_version INTEGER NOT NULL,
        protocol_version TEXT NOT NULL,
        generated_at TEXT NOT NULL,
        checksum_sha256 TEXT NOT NULL,
        payload_json TEXT NOT NULL,
        PRIMARY KEY (event_id, snapshot_version),
        FOREIGN KEY (event_id) REFERENCES events(event_id) ON DELETE CASCADE
    );
    CREATE TABLE IF NOT EXISTS audit_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_id TEXT NOT NULL,
        action TEXT NOT NULL,
        entity_type TEXT NOT NULL,
        entity_id TEXT NOT NULL,
        actor TEXT NOT NULL,
        details_json TEXT NOT NULL,
        occurred_at TEXT NOT NULL,
        FOREIGN KEY (event_id) REFERENCES events(event_id) ON DELETE CASCADE
    );
    CREATE INDEX IF NOT EXISTS idx_contacts_event_evolution ON contacts(event_id, evolution);
    CREATE INDEX IF NOT EXISTS idx_audit_event_time ON audit_log(event_id, occurred_at);
    """,
    2: """
    CREATE TABLE IF NOT EXISTS exposures (
        exposure_id TEXT NOT NULL,
        event_id TEXT NOT NULL,
        contact_id TEXT NOT NULL,
        source_case_id TEXT NOT NULL,
        start_date TEXT NOT NULL,
        end_date TEXT NOT NULL,
        exposure_type TEXT NOT NULL,
        location TEXT,
        notes TEXT,
        created_at TEXT NOT NULL,
        PRIMARY KEY (event_id, exposure_id),
        FOREIGN KEY (event_id, contact_id) REFERENCES contacts(event_id, contact_id) ON DELETE CASCADE
    );
    CREATE INDEX IF NOT EXISTS idx_exposures_contact_dates
        ON exposures(event_id, contact_id, end_date);
    """
}
