"""Collect public legal documents of 8 types and write data/documents.csv.gz.

Sources and licenses:
- Federal Register API (federalregister.gov): U.S. government works, public domain.
  Types: final rule, proposed rule, agency notice, executive order, proclamation, presidential memorandum.
- Caselaw Access Project (static.case.law), Federal Reporter 3d: public domain. Type: court opinion.
- CUAD v1 (Atticus Project, Zenodo record 4595826): CC BY 4.0. Type: contract.

Text that announces the type outright is removed (GPO section banners, the ACTION line, and phrases
such as "final rule" or "executive order"), so the classifier has to use the substance.

Usage:  python -m legal.collect --per-class 250
"""

from __future__ import annotations

import argparse
import html
import json
import random
import re
import time
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

import pandas as pd

from legal.config import CLASSES, DATA_FILE, HEAD_CHARS, RAW_DIR

FR_API = "https://www.federalregister.gov/api/v1/documents.json"
FR_TYPES = {
    "final_rule": {"type": "RULE"},
    "proposed_rule": {"type": "PRORULE"},
    "agency_notice": {"type": "NOTICE"},
    "executive_order": {"type": "PRESDOCU", "presidential_document_type": "executive_order"},
    "proclamation": {"type": "PRESDOCU", "presidential_document_type": "proclamation"},
    "presidential_memorandum": {"type": "PRESDOCU", "presidential_document_type": "memorandum"},
}
CAP_VOLUMES = [500, 520, 540, 560, 580, 600]          # F.3d volumes
CUAD_URL = "https://zenodo.org/records/4595826/files/CUAD_v1.zip?download=1"
USER_AGENT = "legal-document-classifier research (github.com/johnathan-horner/legal-document-classifier)"

TYPE_PHRASES = re.compile(
    r"\b(interim final rule|final rules?|direct final rule|proposed rules?|proposed rulemaking|"
    r"notice of proposed rulemaking|advance notice of proposed rulemaking|executive orders?|proclamations?|"
    r"presidential memorandum|memorandum for|memorandum on|memorandum of)\b",
    re.IGNORECASE,
)


def fetch(url: str, retries: int = 3) -> bytes:
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read()
        except Exception:  # retry any network error
            if attempt == retries - 1:
                raise
            time.sleep(2 * (attempt + 1))
    raise RuntimeError("unreachable")


def clean_federal_register(raw: str) -> str:
    """Drop the GPO wrapper and explicit type statements, keep the document's own text."""
    text = html.unescape(re.sub(r"<[^>]+>", "", raw))
    if "[FR Doc No:" in text:
        text = text.split("[FR Doc No:", 1)[1].split("]", 1)[1]
    drop = re.compile(r"^\s*(\[\[Page \d+\]\]|\[FR Doc\..*|BILLING CODE.*|Vol\. \d+|No\. \d+|Part [IVX]+|"
                      r"Rules and Regulations|Proposed Rules|Notices|Presidential Documents|"
                      r"(Monday|Tuesday|Wednesday|Thursday|Friday),?|[=-]{10,})\s*$")
    lines = [ln for ln in text.splitlines() if not drop.match(ln)]
    text = "\n".join(lines)
    text = re.sub(r"(?im)^\s*ACTION:.*$", "", text)
    text = TYPE_PHRASES.sub("[TYPE]", text)
    return normalize(text)


def normalize(text: str) -> str:
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text)
    return text.strip()


def federal_register(label: str, n: int, rng: random.Random) -> list[dict]:
    cond = FR_TYPES[label]
    docs, page = [], 1
    while len(docs) < n and page <= 20:
        q = {"per_page": 100, "page": page, "order": "newest", "fields[]": ["document_number", "raw_text_url",
             "title", "publication_date", "agencies"], "conditions[type][]": cond["type"],
             "conditions[publication_date][gte]": "2015-01-01"}
        if "presidential_document_type" in cond:
            q["conditions[presidential_document_type][]"] = cond["presidential_document_type"]
        results = json.loads(fetch(FR_API + "?" + urllib.parse.urlencode(q, doseq=True)))["results"]
        if not results:
            break
        rng.shuffle(results)
        for r in results:
            if len(docs) >= n:
                break
            cache = RAW_DIR / "fr" / f"{r['document_number']}.txt"
            if not cache.exists():
                cache.parent.mkdir(parents=True, exist_ok=True)
                cache.write_bytes(fetch(r["raw_text_url"]))
                time.sleep(0.2)
            text = clean_federal_register(cache.read_text(errors="ignore"))
            if len(text) < 400:
                continue
            agency = (r.get("agencies") or [{}])[0].get("name", "")
            docs.append({"doc_id": f"FR-{r['document_number']}", "label": label, "text": text[:HEAD_CHARS],
                         "source": "Federal Register", "license": "Public domain (U.S. government work)",
                         "group": agency or label, "url": r["raw_text_url"]})
        page += 1
        print(f"  {label}: {len(docs)}", flush=True)
    return docs


def court_opinions(n: int, rng: random.Random) -> list[dict]:
    docs = []
    for vol in CAP_VOLUMES:
        cache = RAW_DIR / "cap" / f"f3d-{vol}.zip"
        if not cache.exists():
            cache.parent.mkdir(parents=True, exist_ok=True)
            cache.write_bytes(fetch(f"https://static.case.law/f3d/{vol}.zip"))
        with zipfile.ZipFile(cache) as z:
            for name in sorted(z.namelist()):
                if not (name.startswith("json/") and name.endswith(".json")):
                    continue
                case = json.loads(z.read(name))
                ops = (case.get("casebody") or {}).get("opinions") or []
                body = "\n\n".join(o.get("text", "") for o in ops)
                if len(body) < 1500:
                    continue
                court = (case.get("court") or {}).get("name", "")
                docs.append({"doc_id": f"CAP-{case['id']}", "label": "court_opinion", "text": normalize(body)[:HEAD_CHARS],
                             "source": "Caselaw Access Project (F.3d)", "license": "Public domain",
                             "group": court, "url": f"https://static.case.law/f3d/{vol}/"})
    rng.shuffle(docs)
    return docs[:n]


def contracts(n: int, rng: random.Random) -> list[dict]:
    cache = RAW_DIR / "cuad" / "CUAD_v1.zip"
    if not cache.exists():
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_bytes(fetch(CUAD_URL))
    docs = []
    with zipfile.ZipFile(cache) as z:
        for name in sorted(z.namelist()):
            if "/full_contract_txt/" not in name or not name.endswith(".txt"):
                continue
            text = normalize(z.read(name).decode("utf-8", errors="ignore"))
            if len(text) < 1500:
                continue
            docs.append({"doc_id": "CUAD-" + Path(name).stem[:80], "label": "contract", "text": text[:HEAD_CHARS],
                         "source": "CUAD v1", "license": "CC BY 4.0 (The Atticus Project)",
                         "group": Path(name).parent.name, "url": "https://zenodo.org/records/4595826"})
    rng.shuffle(docs)
    return docs[:n]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--per-class", type=int, default=250)
    parser.add_argument("--seed", type=int, default=13)
    args = parser.parse_args()
    rng = random.Random(args.seed)

    rows = []
    for label in FR_TYPES:
        print(f"Federal Register {label}", flush=True)
        rows += federal_register(label, args.per_class, rng)
    print("court opinions", flush=True)
    rows += court_opinions(args.per_class, rng)
    print("contracts", flush=True)
    rows += contracts(args.per_class, rng)

    df = pd.DataFrame(rows).drop_duplicates("text").reset_index(drop=True)
    assert set(df.label) <= set(CLASSES), set(df.label) - set(CLASSES)
    DATA_FILE.parent.mkdir(exist_ok=True)
    df.to_csv(DATA_FILE, index=False, compression="gzip")
    print(df.label.value_counts().to_string())
    print(f"-> {DATA_FILE}")


if __name__ == "__main__":
    main()
