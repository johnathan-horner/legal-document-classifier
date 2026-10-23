"""Train the classifier, pick the review threshold on validation, report per-class accuracy on test.

Split: stratified by type and grouped by agency (rules, proposed rules, notices) or court (opinions),
so near-identical documents from one agency or court cannot appear on both sides. 60% train,
20% validation, 20% test, fixed seed.

Usage:  python -m legal.train
"""

from __future__ import annotations

import json
import time
from datetime import UTC, datetime

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_recall_fscore_support
from sklearn.model_selection import StratifiedGroupKFold

from legal.classifier import DocumentClassifier
from legal.config import CLASSES, DATA_FILE, METRICS_FILE, MODEL_VERSION

AUTO_ACCURACY_TARGET = 0.98
C_GRID = (1.0, 10.0, 50.0)


def split_groups(df: pd.DataFrame) -> np.ndarray:
    """Use the agency/court group when a type has many of them, otherwise each document is its own group."""
    groups = df["group"].fillna("").astype(str).copy()
    for label, g in df.groupby("label"):
        if g["group"].nunique() < 10:
            groups[g.index] = g["doc_id"]
    return groups.to_numpy()


def make_splits(df: pd.DataFrame, seed: int = 0):
    sgkf = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=seed)
    folds = [test for _, test in sgkf.split(df, df["label"], split_groups(df))]
    test_idx, val_idx = folds[0], folds[1]
    train_idx = np.setdiff1d(np.arange(len(df)), np.concatenate([test_idx, val_idx]))
    return df.iloc[train_idx], df.iloc[val_idx], df.iloc[test_idx]


def pick_threshold(conf: np.ndarray, correct: np.ndarray, target: float = AUTO_ACCURACY_TARGET,
                   min_cases: int = 20) -> float:
    for t in np.unique(np.round(conf, 4)):
        auto = conf >= t
        if auto.sum() < min_cases:
            break
        if correct[auto].mean() >= target:
            return float(t)
    return 1.01


def lane_report(conf, correct, threshold) -> dict:
    out = {}
    for name, mask in (("auto", conf >= threshold), ("review_queue", conf < threshold)):
        n = int(mask.sum())
        out[name] = {"documents": n, "share": round(n / len(conf), 4),
                     "accuracy": round(float(correct[mask].mean()), 4) if n else None}
    return out


def main() -> None:
    started = time.time()
    df = pd.read_csv(DATA_FILE)
    train, val, test = make_splits(df)

    # Pick C on validation.
    best = None
    for C in C_GRID:
        clf = DocumentClassifier.train(train.text.tolist(), train.label.tolist(), C=C)
        acc = accuracy_score(val.label, np.array(clf.classes)[clf.proba(val.text.tolist()).argmax(1)])
        if best is None or acc > best[1]:
            best = (C, acc, clf)
    C, val_acc, clf = best

    p_val = clf.proba(val.text.tolist())
    val_pred = np.array(clf.classes)[p_val.argmax(1)]
    clf.threshold = pick_threshold(p_val.max(1), val_pred == val.label.to_numpy())

    p_test = clf.proba(test.text.tolist())
    pred = np.array(clf.classes)[p_test.argmax(1)]
    y = test.label.to_numpy()
    conf = p_test.max(1)
    prec, rec, f1, support = precision_recall_fscore_support(y, pred, labels=list(CLASSES), zero_division=0)
    per_class = {c: {"documents": int(s), "accuracy": round(float(r), 4), "precision": round(float(p), 4),
                     "f1": round(float(f), 4)} for c, p, r, f, s in zip(CLASSES, prec, rec, f1, support)}

    metrics = {
        "model_version": MODEL_VERSION,
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "data": {"documents": len(df), "per_class": df.label.value_counts().to_dict(),
                 "sources": df.groupby("source")["license"].first().to_dict(),
                 "split": {"train": len(train), "validation": len(val), "test": len(test)},
                 "split_method": "StratifiedGroupKFold (5 folds, seed 0): fold 0 test, fold 1 validation, "
                                 "rest train; grouped by agency or court"},
        "model": {"C": C, "validation_accuracy": round(float(val_acc), 4)},
        "routing": {"threshold": round(clf.threshold, 4),
                    "rule": f"lowest confidence with >= {AUTO_ACCURACY_TARGET:.0%} accuracy on auto-routed "
                            "validation documents",
                    "test": lane_report(conf, pred == y, clf.threshold)},
        "test": {"accuracy": round(float(accuracy_score(y, pred)), 4),
                 "macro_f1": round(float(f1_score(y, pred, average="macro")), 4),
                 "per_class": per_class,
                 "confusion_matrix": {"labels": list(CLASSES),
                                      "rows_true_cols_pred": confusion_matrix(y, pred, labels=list(CLASSES)).tolist()}},
        "wall_clock_seconds": round(time.time() - started, 1),
    }
    clf.save()
    METRICS_FILE.write_text(json.dumps(metrics, indent=2) + "\n")
    print(json.dumps({k: metrics[k] for k in ("model", "routing", "test")}, indent=2))


if __name__ == "__main__":
    main()
