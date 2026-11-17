# Arrow verification: Legal Document Type Classifier

Diagram: `docs/architecture/architecture.png` (What runs today, no AWS at runtime).
Code read from `origin/main` at 9190b62. No arrow touches an AWS service, so no AWS doc applies.
No second diagram: there is no IaC (CDK, Terraform, SAM) on main.

| From | To | Action | Code evidence | AWS doc |
|---|---|---|---|---|
| Visitor / reviewer | Streamlit app | Paste text, upload .txt/.pdf (first 10 PDF pages) or pick a held-out example; confirm or correct a queued type | app.py:50-67 (inputs), app.py:37-43 (PDF read, `pages[:10]`), app.py:92-104 (review tab, `Save review`) | N/A (not AWS) |
| Streamlit app | Audit log (SQLite) | Writes a `classified` row (SHA-256 of text, never the text; `pending` if routed to review) and, on review, a `review` row (`confirmed`/`corrected`) | app.py:72 `audit.record_classification(...)`, app.py:103 `audit.record_review(...)`; legal/audit.py:50-58, 60-67; DB path app.py:26 (`LEGAL_AUDIT_DB`, default `audit_log.sqlite3`) | N/A (not AWS) |
| Audit log | Review queue | Query: latest row per document where `reviewer_action = 'pending'`, lowest confidence first | legal/audit.py:80-88; app.py:93 | N/A (not AWS) |
| Streamlit app | documents.csv.gz | Reads the dataset, rebuilds the split, shows 3 test-split examples per type | app.py:29-34 (`make_splits(pd.read_csv(DATA_FILE))`, `groupby("label").head(3)`); legal/config.py:6 | N/A (not AWS) |
| Streamlit app | artifacts/ (classifier.joblib + metrics.json) | Loads the joblib pipeline and calls `predict` (first 6,000 chars; type, confidence, top 3, evidence terms; route by threshold); reads metrics.json for the Test results tab | app.py:19-21 (`DocumentClassifier.load()`), app.py:71; legal/classifier.py:45-68, 74-76; legal/config.py:9-10,14; app.py:116-117 | N/A (not AWS) |
| Public sources (Federal Register API, Caselaw Access Project, CUAD on Zenodo) | legal/collect.py | HTTPS GET downloads with `urllib.request` (build time only, run by hand via `python -m legal.collect`) | legal/collect.py:32 (FR API), :42 (CUAD URL), :53-63 (`fetch`), :96, :106, :126, :148 | N/A (not AWS) |
| legal/collect.py | legal/train.py | Writes `data/documents.csv.gz`, which train reads | legal/collect.py:180-183; legal/train.py:67 | N/A (not AWS) |
| legal/train.py | artifacts/ | Writes `classifier.joblib` and `metrics.json` (committed to the repo; README.md:88-89) | legal/train.py:111-112; legal/classifier.py:70-72 | N/A (not AWS) |

UNVERIFIED arrows: none (no AWS arrows).
