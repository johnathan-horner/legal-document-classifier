"""Legal Document Type Classifier: what runs today (traced from origin/main).

Run from this directory:  python architecture.py
"""
from diagrams.aws.general import User

from archstyle import arch, box, e, layer, linkedin, outside

OUT = "architecture"
with arch("Legal Document Type Classifier", "What runs today (no AWS at runtime)", OUT):
    user = User("Visitor / reviewer")

    with outside("Streamlit Community Cloud"):
        with layer("App", margin=40):
            app = box("Streamlit app (app.py)\nClassify | Review queue |\nAudit log | Test results")
        with layer("Governance"):
            audit = box("Audit log (SQLite)\nappend-only rows\nSHA-256 of text, no text")
            queue = box("Review queue\nlatest row still 'pending'\n(confidence < 0.513)")
        with layer("Committed artifacts", margin=36):
            data = box("documents.csv.gz\n2,000 public documents\n(held-out examples)")
            model = box("artifacts/\nclassifier.joblib: TF-IDF +\nlogistic regression (scikit-learn)\nmetrics.json: test results")

    offline = outside("Offline build (not at runtime)")
    offline.dot.graph_attr["labeljust"] = "r"  # keep the outgoing arrow clear of the label
    with offline:
        sources = box("Federal Register API\nCaselaw Access Project\nCUAD v1 (Zenodo)")
        collect = box("legal/collect.py\ndownload + strip type markers")
        train = box("legal/train.py\ngrouped split, pick C + threshold")

    user >> e("paste, upload .txt/.pdf or pick example;\nconfirm or correct queued types") >> app
    app >> e("writes 'classified' and\n'review' rows") >> audit
    audit >> e("latest row per doc\nwhere pending") >> queue
    app >> e("reads test-split\nexamples") >> data
    app >> e("predict (first 6,000 chars):\ntype, confidence, top 3, evidence;\nreads metrics") >> model

    sources >> e("HTTPS downloads\n(build time only)") >> collect
    collect >> e("writes dataset") >> train
    train >> e("writes model + metrics\n(committed to repo)") >> model

linkedin(OUT)
