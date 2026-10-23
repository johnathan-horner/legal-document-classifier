"""Streamlit demo: classify a legal document by type, route low-confidence ones to review, log everything."""

from __future__ import annotations

import io
import json
import os

import pandas as pd
import streamlit as st

from legal.audit import AuditLog
from legal.classifier import DocumentClassifier, display
from legal.config import CLASSES, DATA_FILE, METRICS_FILE, ROUTE_AUTO

st.set_page_config(page_title="Legal Document Type Classifier", layout="wide")


@st.cache_resource
def get_classifier() -> DocumentClassifier:
    return DocumentClassifier.load()


@st.cache_resource
def get_audit() -> AuditLog:
    return AuditLog(os.environ.get("LEGAL_AUDIT_DB", "audit_log.sqlite3"))


@st.cache_data
def get_examples() -> pd.DataFrame:
    from legal.train import make_splits

    _, _, test = make_splits(pd.read_csv(DATA_FILE))
    return test.groupby("label").head(3).reset_index(drop=True)


def read_upload(upload) -> str:
    data = upload.getvalue()
    if upload.name.lower().endswith(".pdf"):
        from pypdf import PdfReader

        return "\n".join(page.extract_text() or "" for page in PdfReader(io.BytesIO(data)).pages[:10])
    return data.decode("utf-8", errors="ignore")


def classify_tab(clf: DocumentClassifier, audit: AuditLog) -> None:
    examples = get_examples()
    left, right = st.columns([1, 1])
    with left:
        source = st.radio("Document", ["Held-out test example", "Paste text", "Upload .txt or .pdf"], horizontal=True)
        text, name, truth = "", "", None
        if source == "Held-out test example":
            options = [f"{display(r.label)}: {r.doc_id}" for r in examples.itertuples()]
            choice = st.selectbox("Example (from the test split)", options)
            row = examples.iloc[options.index(choice)]
            text, name, truth = row.text, row.doc_id, row.label
            st.caption(f"Source: {row.source} ({row.license}). True type is hidden from the model.")
        elif source == "Paste text":
            text = st.text_area("Document text", height=260)
            name = "pasted text"
        else:
            upload = st.file_uploader("Document", type=["txt", "pdf"])
            if upload:
                text, name = read_upload(upload), upload.name
        if text:
            st.text_area("First 1,500 characters", text[:1500], height=260, disabled=True)
        run = st.button("Classify", type="primary", disabled=not text.strip())

    with right:
        if run:
            pred = clf.predict(text)
            doc_id = audit.record_classification(text, clf.version, pred.label, pred.confidence, pred.route, name)
            st.session_state["last"] = (doc_id, pred, truth)
        if "last" not in st.session_state:
            st.info("Pick a document and press Classify.")
            return
        doc_id, pred, truth = st.session_state["last"]
        st.subheader(display(pred.label))
        st.metric("Confidence", f"{pred.confidence:.1%}")
        if pred.route == ROUTE_AUTO:
            st.success(f"Auto-routed (confidence at or above {clf.threshold:.1%})")
        else:
            st.warning(f"Sent to review queue (confidence below {clf.threshold:.1%})")
        st.markdown("**Top 3**")
        st.dataframe(pd.DataFrame([{"type": display(c), "probability": p} for c, p in pred.top3]), hide_index=True)
        if pred.evidence:
            st.markdown("**Terms that pointed to this type:** " + ", ".join(f"`{t}`" for t in pred.evidence))
        if truth:
            st.caption(f"True type: {display(truth)}. Document {doc_id} logged.")


def review_tab(audit: AuditLog) -> None:
    queue = audit.review_queue()
    st.write(f"{len(queue)} document(s) waiting for review.")
    reviewer = st.text_input("Reviewer", value="demo-reviewer")
    for item in queue:
        with st.container(border=True):
            st.markdown(f"**{item['document_id']}** ({item['source_name']}): model says "
                        f"**{display(item['predicted_type'])}** at {item['confidence']:.1%}")
            choice = st.selectbox("Correct type", CLASSES, index=CLASSES.index(item["predicted_type"]),
                                  format_func=display, key=f"t-{item['document_id']}")
            if st.button("Save review", key=f"b-{item['document_id']}"):
                audit.record_review(item["document_id"], reviewer, choice)
                st.rerun()


def audit_tab(audit: AuditLog) -> None:
    events = pd.DataFrame(audit.events())
    if events.empty:
        st.info("Nothing classified yet.")
        return
    st.dataframe(events.iloc[::-1], hide_index=True, width="stretch")
    st.download_button("Download CSV", events.to_csv(index=False), "audit_log.csv", "text/csv")


def results_tab() -> None:
    m = json.loads(METRICS_FILE.read_text())
    t, r, d = m["test"], m["routing"], m["data"]
    st.markdown(f"{d['documents']:,} public documents in 8 types. Test split: {d['split']['test']} documents "
                f"never used for training or threshold choice. {d['split_method']}.")
    c1, c2, c3 = st.columns(3)
    c1.metric("Test accuracy", f"{t['accuracy']:.1%}")
    c2.metric("Macro F1", f"{t['macro_f1']:.3f}")
    c3.metric("Review threshold", f"{r['threshold']:.3f}")
    st.markdown("**Per-class results on the test split**")
    st.dataframe(pd.DataFrame(t["per_class"]).T.rename(index=display), width="stretch")
    st.markdown(f"**Routing on the test split** ({r['rule']})")
    st.dataframe(pd.DataFrame(r["test"]).T, width="stretch")
    cm = t["confusion_matrix"]
    st.markdown("**Confusion matrix** (rows are the true type)")
    st.dataframe(pd.DataFrame(cm["rows_true_cols_pred"], index=[display(x) for x in cm["labels"]],
                              columns=[display(x) for x in cm["labels"]]), width="stretch")


def main() -> None:
    st.title("Legal Document Type Classifier")
    st.info("Built on public legal documents. A routing aid for document intake, not legal advice.")
    clf, audit = get_classifier(), get_audit()
    tabs = st.tabs(["Classify", "Review queue", "Audit log", "Test results"])
    with tabs[0]:
        classify_tab(clf, audit)
    with tabs[1]:
        review_tab(audit)
    with tabs[2]:
        audit_tab(audit)
    with tabs[3]:
        results_tab()


main()
