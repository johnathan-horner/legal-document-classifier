"""Legal Document Classifier: training pipeline (offline) and the live app. No AWS services."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from diagrams import Diagram
from diagrams.onprem.client import User

from style import EDGE, GRAPH, NODE, area, flow, icon, primary, soft

with Diagram("Legal Document Classifier  |  Live architecture",
             filename=str(Path(__file__).with_name("architecture")), outformat="png", direction="TB",
             show=False, graph_attr=GRAPH, node_attr=NODE, edge_attr=EDGE):
    user = User("Legal ops user\n(browser)")

    with area("Training  (offline, laptop CPU)", "plan"):
        sources = icon("file-search-green", "2,000 public documents\nFederal Register, Caselaw\nAccess Project, CUAD")
        clean = icon("list-checks-ink", "Strip type giveaways\nsplit by agency or court")
        train = icon("scikitlearn", "TF-IDF + logistic\nregression")
        model = icon("layers-green", "Model file in repo\nthreshold 0.513")

    with area("Streamlit Community Cloud", "host"):
        app = icon("streamlit", "Streamlit app\nclassify, review queue,\naudit log, results")
        clf = icon("scikitlearn", "Classifier\n8 document types,\ntop 3 + key words")
        with area("Routing lanes"):
            auto = icon("list-checks-ink", "Auto-routed\n84.5% of test docs")
            queue = icon("user-check-ink", "Review queue\nperson confirms\nor corrects")
        with area("Audit"):
            audit = icon("sqlite", "Audit log (SQLite)\nappend-only, stores\nSHA-256 hash, not text")

    sources >> flow("collect") >> clean
    clean >> flow("train / val / test") >> train
    train >> flow("save") >> model
    model >> soft("loaded at startup") >> clf

    user >> flow("text, .txt or .pdf\n(first 10 pages)") >> app
    app >> primary("document text") >> clf
    clf >> flow("confidence at or above") >> auto
    clf >> flow("below") >> queue
    auto >> flow("classification") >> audit
    queue >> flow("classification + review") >> audit
