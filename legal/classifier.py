"""TF-IDF + logistic regression document-type classifier with confidence routing and term-level reasons."""

from __future__ import annotations

from dataclasses import dataclass, field

import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from legal.config import HEAD_CHARS, LABELS, MODEL_FILE, MODEL_VERSION, ROUTE_AUTO, ROUTE_REVIEW


@dataclass
class Prediction:
    label: str
    confidence: float
    route: str
    top3: list[tuple[str, float]]
    evidence: list[str] = field(default_factory=list)   # terms that pushed toward the predicted type


@dataclass
class DocumentClassifier:
    pipeline: Pipeline
    threshold: float = 1.01
    version: str = MODEL_VERSION

    @classmethod
    def train(cls, texts, labels, C: float = 10.0, seed: int = 0) -> DocumentClassifier:
        pipe = Pipeline([
            ("tfidf", TfidfVectorizer(sublinear_tf=True, ngram_range=(1, 2), min_df=2, max_df=0.9,
                                      max_features=150_000, strip_accents="unicode")),
            ("clf", LogisticRegression(C=C, max_iter=3000, random_state=seed)),
        ])
        pipe.fit([t[:HEAD_CHARS] for t in texts], labels)
        return cls(pipe)

    @property
    def classes(self) -> list[str]:
        return list(self.pipeline.classes_)

    def proba(self, texts) -> np.ndarray:
        return self.pipeline.predict_proba([t[:HEAD_CHARS] for t in texts])

    def route(self, confidence: float) -> str:
        return ROUTE_AUTO if confidence >= self.threshold else ROUTE_REVIEW

    def evidence(self, text: str, label: str, top: int = 6) -> list[str]:
        """Terms in this document with the largest positive contribution to `label`."""
        tfidf, clf = self.pipeline.named_steps["tfidf"], self.pipeline.named_steps["clf"]
        x = tfidf.transform([text[:HEAD_CHARS]])
        coef = clf.coef_[self.classes.index(label)]
        contrib = x.multiply(coef).tocsr()
        idx = contrib.indices[np.argsort(-contrib.data)][:top]
        vocab = tfidf.get_feature_names_out()
        return [vocab[i] for i in idx if contrib[0, i] > 0]

    def predict(self, text: str) -> Prediction:
        p = self.proba([text])[0]
        order = np.argsort(-p)
        label = self.classes[order[0]]
        conf = float(p[order[0]])
        return Prediction(label, conf, self.route(conf),
                          [(self.classes[i], round(float(p[i]), 4)) for i in order[:3]],
                          self.evidence(text, label))

    def save(self, path=MODEL_FILE) -> None:
        path.parent.mkdir(exist_ok=True)
        joblib.dump(self, path, compress=3)

    @staticmethod
    def load(path=MODEL_FILE) -> DocumentClassifier:
        return joblib.load(path)


def display(label: str) -> str:
    return LABELS.get(label, label)
