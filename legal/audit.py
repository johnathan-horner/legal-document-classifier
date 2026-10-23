"""Append-only audit log in SQLite. Each classification and each reviewer decision is a new row."""

from __future__ import annotations

import hashlib
import sqlite3
import uuid
from datetime import UTC, datetime
from pathlib import Path

from legal.config import AUDIT_DB, ROUTE_REVIEW

SCHEMA = """
CREATE TABLE IF NOT EXISTS audit_events (
    event_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id     TEXT NOT NULL,
    text_sha256     TEXT NOT NULL,      -- the text itself is not stored
    event_type      TEXT NOT NULL CHECK (event_type IN ('classified', 'review')),
    model_version   TEXT NOT NULL,
    predicted_type  TEXT NOT NULL,
    confidence      REAL NOT NULL,
    route           TEXT NOT NULL,
    reviewer_action TEXT NOT NULL,      -- none, pending, confirmed, corrected
    reviewer_type   TEXT,
    reviewer        TEXT,
    source_name     TEXT,
    created_at      TEXT NOT NULL
);
"""
COLUMNS = ("event_id", "document_id", "text_sha256", "event_type", "model_version", "predicted_type", "confidence",
           "route", "reviewer_action", "reviewer_type", "reviewer", "source_name", "created_at")


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


class AuditLog:
    def __init__(self, path: Path | str = AUDIT_DB):
        self.path = str(path)
        with sqlite3.connect(self.path) as conn:
            conn.executescript(SCHEMA)

    def _insert(self, row: dict) -> None:
        cols = [c for c in COLUMNS if c != "event_id"]
        with sqlite3.connect(self.path) as conn:
            conn.execute(f"INSERT INTO audit_events ({', '.join(cols)}) VALUES ({', '.join('?' * len(cols))})",
                         [row.get(c) for c in cols])

    def record_classification(self, text: str, model_version: str, predicted_type: str, confidence: float,
                              route: str, source_name: str = "") -> str:
        doc_id = "doc-" + uuid.uuid4().hex[:12]
        self._insert({"document_id": doc_id, "text_sha256": hashlib.sha256(text.encode()).hexdigest(),
                      "event_type": "classified", "model_version": model_version, "predicted_type": predicted_type,
                      "confidence": confidence, "route": route,
                      "reviewer_action": "pending" if route == ROUTE_REVIEW else "none",
                      "source_name": source_name, "created_at": _now()})
        return doc_id

    def record_review(self, document_id: str, reviewer: str, reviewer_type: str) -> str:
        latest = self.latest(document_id)
        if latest is None:
            raise KeyError(f"unknown document {document_id}")
        action = "confirmed" if reviewer_type == latest["predicted_type"] else "corrected"
        self._insert({**latest, "event_type": "review", "reviewer_action": action, "reviewer_type": reviewer_type,
                      "reviewer": reviewer, "created_at": _now()})
        return action

    def events(self, document_id: str | None = None) -> list[dict]:
        sql, args = f"SELECT {', '.join(COLUMNS)} FROM audit_events", ()
        if document_id:
            sql, args = sql + " WHERE document_id = ?", (document_id,)
        with sqlite3.connect(self.path) as conn:
            return [dict(zip(COLUMNS, r)) for r in conn.execute(sql + " ORDER BY event_id", args)]

    def latest(self, document_id: str) -> dict | None:
        rows = self.events(document_id)
        return rows[-1] if rows else None

    def review_queue(self) -> list[dict]:
        sql = f"""
            SELECT {', '.join('e.' + c for c in COLUMNS)} FROM audit_events e
            JOIN (SELECT document_id, MAX(event_id) AS last_id FROM audit_events GROUP BY document_id) l
              ON e.event_id = l.last_id
            WHERE e.reviewer_action = 'pending' ORDER BY e.confidence
        """
        with sqlite3.connect(self.path) as conn:
            return [dict(zip(COLUMNS, r)) for r in conn.execute(sql)]
