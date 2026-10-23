"""Paths and constants."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT / "data" / "documents.csv.gz"
RAW_DIR = ROOT / ".raw"                     # downloads cache, not committed
ARTIFACTS = ROOT / "artifacts"
MODEL_FILE = ARTIFACTS / "classifier.joblib"
METRICS_FILE = ARTIFACTS / "metrics.json"
AUDIT_DB = ROOT / "audit_log.sqlite3"

MODEL_VERSION = "tfidf-logreg-v1"
HEAD_CHARS = 6000                           # the classifier reads the first 6,000 characters

CLASSES = (
    "contract",
    "court_opinion",
    "final_rule",
    "proposed_rule",
    "agency_notice",
    "executive_order",
    "proclamation",
    "presidential_memorandum",
)
LABELS = {
    "contract": "Contract",
    "court_opinion": "Court opinion",
    "final_rule": "Final rule",
    "proposed_rule": "Proposed rule",
    "agency_notice": "Agency notice",
    "executive_order": "Executive order",
    "proclamation": "Proclamation",
    "presidential_memorandum": "Presidential memorandum",
}

ROUTE_AUTO = "auto"
ROUTE_REVIEW = "review_queue"
