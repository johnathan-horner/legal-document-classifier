"""Uses the committed model (artifacts/) and dataset."""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from legal.audit import AuditLog
from legal.classifier import DocumentClassifier
from legal.config import CLASSES, DATA_FILE, METRICS_FILE, ROUTE_AUTO, ROUTE_REVIEW
from legal.train import make_splits, pick_threshold


@pytest.fixture(scope="module")
def clf():
    return DocumentClassifier.load()


@pytest.fixture(scope="module")
def test_split():
    return make_splits(pd.read_csv(DATA_FILE))[2]


def test_prediction_shape(clf, test_split):
    pred = clf.predict(test_split.text.iloc[0])
    assert pred.label in CLASSES
    assert 0 < pred.confidence <= 1
    assert pred.route in (ROUTE_AUTO, ROUTE_REVIEW)
    assert len(pred.top3) == 3 and pred.top3[0][0] == pred.label
    assert all(isinstance(t, str) for t in pred.evidence)


def test_reported_accuracy_reproduces(clf, test_split):
    m = json.loads(METRICS_FILE.read_text())
    proba = clf.proba(test_split.text.tolist())
    acc = (np.array(clf.classes)[proba.argmax(1)] == test_split.label.to_numpy()).mean()
    assert round(float(acc), 4) == m["test"]["accuracy"]
    assert m["routing"]["threshold"] == round(clf.threshold, 4)


def test_low_confidence_goes_to_review(clf):
    clf_copy = DocumentClassifier(clf.pipeline, threshold=0.9)
    assert clf_copy.route(0.95) == ROUTE_AUTO
    assert clf_copy.route(0.5) == ROUTE_REVIEW


def test_unrelated_text_is_not_confident(clf):
    pred = clf.predict("Preheat the oven to 350 degrees. Mix flour, sugar and eggs, then bake for 30 minutes.")
    assert pred.confidence < clf.threshold


def test_pick_threshold():
    conf = np.array([0.99] * 30 + [0.6] * 10)
    correct = np.array([True] * 30 + [False] * 10)
    assert pick_threshold(conf, correct, 0.98) == 0.99
    assert pick_threshold(np.full(40, 0.9), np.zeros(40, bool)) == 1.01


def test_audit_is_append_only_and_stores_no_text(tmp_path):
    audit = AuditLog(tmp_path / "a.sqlite3")
    doc = audit.record_classification("secret contents", "v1", "contract", 0.55, ROUTE_REVIEW, "x.txt")
    assert [q["document_id"] for q in audit.review_queue()] == [doc]
    assert audit.record_review(doc, "rev", "court_opinion") == "corrected"
    events = audit.events(doc)
    assert [e["event_type"] for e in events] == ["classified", "review"]
    assert events[0]["reviewer_action"] == "pending"
    assert "secret" not in json.dumps(events)
    assert audit.review_queue() == []


def test_app_classifies_an_example(tmp_path, monkeypatch):
    monkeypatch.setenv("LEGAL_AUDIT_DB", str(tmp_path / "app.sqlite3"))
    at = AppTest.from_file(str(Path(__file__).parent.parent / "app.py"), default_timeout=180).run()
    assert not at.exception
    at.button[0].click().run()
    assert not at.exception
    assert at.subheader and at.metric
