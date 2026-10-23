"""Checks on the committed dataset (data/documents.csv.gz)."""
import re

import pandas as pd
import pytest

from legal.collect import TYPE_PHRASES, clean_federal_register
from legal.config import CLASSES, DATA_FILE
from legal.train import make_splits, split_groups


@pytest.fixture(scope="module")
def df():
    return pd.read_csv(DATA_FILE)


def test_all_classes_present_and_balanced(df):
    counts = df["label"].value_counts()
    assert set(counts.index) == set(CLASSES)
    assert counts.min() >= 150


def test_every_document_has_source_and_license(df):
    assert df[["source", "license", "url"]].notna().all().all()
    assert set(df["license"]) <= {"Public domain (U.S. government work)", "Public domain",
                                  "CC BY 4.0 (The Atticus Project)"}


def test_no_explicit_type_markers_in_federal_register_text(df):
    fr = df[df["source"] == "Federal Register"]
    banners = re.compile(r"\[(?:Rules and Regulations|Proposed Rules|Notices|Presidential Documents)\]")
    assert not fr["text"].str.contains(banners).any()
    assert not fr["text"].str.contains(r"(?im)^\s*ACTION:").any()
    assert not fr["text"].apply(lambda t: bool(TYPE_PHRASES.search(t))).any()


def test_no_duplicate_texts(df):
    assert df["text"].is_unique


def test_splits_do_not_share_agencies_or_courts(df):
    train, val, test = make_splits(df)
    groups = pd.Series(split_groups(df), index=df.index)
    for a, b in ((train, test), (train, val), (val, test)):
        assert not set(groups[a.index]) & set(groups[b.index])
    assert len(train) + len(val) + len(test) == len(df)


def test_cleaner_removes_wrapper_and_markers():
    raw = ("<html><pre>[Federal Register Volume 91]\n[Proposed Rules]\n[FR Doc No: 2026-1]\n"
           "[[Page 5]]\nDEPARTMENT OF X\nACTION: Proposed rule.\nThis proposed rule would change Y.\n"
           "BILLING CODE 1234-56-P\n</pre></html>")
    out = clean_federal_register(raw)
    assert "Proposed Rules" not in out and "ACTION" not in out and "BILLING" not in out
    assert "[TYPE] would change Y." in out and "DEPARTMENT OF X" in out
