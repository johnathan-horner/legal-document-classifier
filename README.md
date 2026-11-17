# Legal Document Type Classifier

![CI](https://github.com/johnathan-horner/legal-document-classifier/actions/workflows/ci.yml/badge.svg)

**Status: Live.** Demo: https://legal-document-classifier.streamlit.app (checked 2026-11-16; the free
Streamlit host puts it to sleep when idle and it wakes on the first visit). The classifier, review
queue, audit log and Streamlit app also run locally.

Independent reference project by Shoot It Analytics LLC. Built with public or synthetic data.

## What it does

1. Reads a legal document (pasted text, a .txt file or the first 10 pages of a .pdf) and predicts its type out of 8:
   contract, court opinion, final rule, proposed rule, agency notice, executive order, proclamation,
   presidential memorandum.
2. Gives the prediction a confidence score and the three most likely types, and lists the words in
   the document that pushed it toward the predicted type.
3. Routes confident predictions to **auto** and low-confidence ones to a **review queue**, where a
   person confirms or corrects the type.
4. Logs every classification and every review to an append-only audit log. The log stores a SHA-256
   hash of the text, not the text itself.

| Auto-routed | Sent to review |
|---|---|
| ![auto](docs/screenshots/01-auto-routed.png) | ![review](docs/screenshots/02-sent-to-review.png) |

| Review queue | Test results |
|---|---|
| ![queue](docs/screenshots/03-review-queue.png) | ![results](docs/screenshots/05-test-results.png) |

## Case study

**Legal Document Type Classifier.** Sorts legal documents into 8 types (contracts, court opinions, rules, notices, presidential documents) with a confidence score, sends unsure ones to a person, and logs every decision without storing the text.

Status: **Live** · [Live app](https://legal-document-classifier.streamlit.app) · [GitHub](https://github.com/johnathan-horner/legal-document-classifier) · [Portfolio](https://portfolio.johnathancloudspace.com/#legal-document-classifier)

### Real-world problem

The Federal Register published 23,690 documents in 2025, including 2,441 rules, 1,498 proposed rules and 19,280 notices ([Federal Register statistics](https://www.federalregister.gov/reader-aids/federal-register-statistics/category-document-statistics)). Legal and compliance teams sort documents like these by type before anyone reads them for substance, and a wrong label sends a document to the wrong queue.

### Why I built it

I wanted to see how far a small, cheap classifier trained on public documents could go, and whether its own confidence could separate the documents it gets right from the ones a person should check, measured on agencies and courts it never saw in training.

### Version 1

The first version was designed as a full AWS pipeline: Textract for OCR, a DistilBERT classifier on SageMaker, three parallel LangGraph agents on ECS Fargate for clause, regulatory and briefing analysis, SQS routing to attorney queues and Cognito access control. The pipeline imported modules that were never in the repo and the app showed mock data, so it never ran end to end. I rebuilt it in October 2026 as a small classifier that actually runs, costs nothing per document, and has results measured on documents it never saw.

### Key decisions

- **TF-IDF and logistic regression instead of an LLM.** It trains in 43 seconds on a laptop CPU, costs nothing per document and shows the terms behind each prediction. It is weaker on documents that differ only in meaning: agency notices are right 56% of the time.
- **Strip the giveaways before training.** Headers and phrases that state the type outright are replaced with [TYPE], and tests check none remain. Scores are lower than on uncleaned text, but they measure substance, not headers.
- **Hold out whole agencies and courts.** For rules, notices and opinions the split is grouped by agency or court, so templated documents from one source can't land in both train and test. Contracts and the three presidential types come from one source each, so they are split per document.
- **Pick the review threshold on validation and use test once.** The threshold is the lowest confidence that gave 98% accuracy on auto-routed validation documents. The cost is that a miss on test stays a miss.

### Architecture

![Legal Document Type Classifier: Live architecture](docs/architecture/architecture.png)

A person pastes text, uploads a .txt or .pdf, or picks a held-out example. The classifier reads the first 6,000 characters and returns a type, a confidence, the top 3 types and the terms behind the call; documents at 0.513 confidence or above go to auto, the rest to the review queue, and every step goes to an append-only SQLite log that stores a SHA-256 of the text. Data collection and training run offline and the model file is committed, so nothing calls out at runtime and no AWS is involved.

### Governance and safety

- Confidence routing: below 0.513 a document goes to a review queue where a person confirms or corrects the type.
- Append-only audit log of every classification and review, with a SHA-256 of the text and never the text itself (tested).
- Leakage guard: tests check no type-announcing text survives cleaning.
- Out-of-domain test: unrelated text (a recipe) must fall below the threshold.
- Labelled in the app as a routing aid for document intake, not legal advice. CI scans the git history for secrets.

### Results

- 432 held-out documents: 90.7% accuracy, macro F1 0.905.
- Routing on test: 84.5% auto-routed at 96.2% accuracy; the 15.5% sent to review were right 61.2% of the time, which is why a person checks them.
- Per class: contracts, court opinions and executive orders 100%; agency notices 56%, the weakest class.
- 13 automated tests in CI.

### What I got wrong

- **I wrote the docs for the target design before it was built.** Now I only document what runs and what's measured.
- **The documents announce their own type.** Federal Register text carries phrases like "final rule" and printing-office banners, so a model can score well by reading headers. Removing them before training lowered the scores and made them honest.
- **The auto lane missed its target.** The review threshold was set for 98% accuracy on auto-routed validation documents. On test the auto lane reached 96.2%. I report the miss instead of retuning on test data.
- **The split depended on the library version.** A different scikit-learn version produced a different train and test split, so the version is pinned and a test checks the split sizes.

### Constraints

- 2,000 public documents only, with each document's license recorded: Federal Register and Caselaw Access Project text is public domain, CUAD contracts are CC BY 4.0.
- No model calls and no network calls at runtime. Data collection and training run offline, and the model file is committed to the repo.
- Runs on a laptop CPU and on the free Streamlit host; training takes 43 seconds.
- Text only: the classifier reads the first 6,000 characters, and only the first 10 pages of a PDF. No OCR.
- Every result has to be measured on agencies and courts held out of training.

### Limits

Built on public documents only (Federal Register, Caselaw Access Project, CUAD), 8 types, first 6,000 characters; not legal advice and not reviewed by any regulator.

### What I'd do in a real deployment

Train on the team's own intake types with reviewer corrections fed back as labels, compare against a small fine-tuned transformer, and run it behind sign-in with a durable audit store.

### Sources

- [Federal Register: Document Count by Category](https://www.federalregister.gov/reader-aids/federal-register-statistics/category-document-statistics)
- [Live app](https://legal-document-classifier.streamlit.app)
- [GitHub](https://github.com/johnathan-horner/legal-document-classifier)
- [Portfolio](https://portfolio.johnathancloudspace.com/#legal-document-classifier)

Built by Johnathan Horner, Shoot It Analytics LLC

## Architecture

The architecture diagram and how it works are in the [Case study](#architecture) above.

## How to run

Python 3.11.

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
streamlit run app.py
pytest
```

Rebuild the dataset and retrain (downloads about 1,500 Federal Register documents, 6 Caselaw volumes
and the 106 MB CUAD archive; took about 40 minutes here, mostly downloads):

```bash
python -m legal.collect --per-class 250
python -m legal.train
```

## Measured results

**How measured.** `python -m legal.train`. 2,000 documents split with `StratifiedGroupKFold`
(5 folds, seed 0), grouped by agency (Federal Register rules and notices) or court (opinions): 1,161
train, 407 validation, 432 test. The regularization strength was picked on validation (C = 10,
91.7% validation accuracy), then the routing threshold on validation. The test split was used once.

Test split, per class:

| Type | Documents | Accuracy | Precision |
|---|---|---|---|
| Contract | 50 | 1.000 | 0.893 |
| Court opinion | 48 | 1.000 | 1.000 |
| Final rule | 54 | 0.870 | 0.870 |
| Proposed rule | 80 | 0.963 | 0.810 |
| Agency notice | 50 | 0.560 | 0.966 |
| Executive order | 50 | 1.000 | 0.862 |
| Proclamation | 50 | 0.980 | 1.000 |
| Presidential memorandum | 50 | 0.860 | 1.000 |
| **All** | **432** | **0.907** | macro F1 0.905 |

Routing on the test split (threshold 0.513):

| Lane | Documents | Share | Accuracy |
|---|---|---|---|
| Auto | 365 | 84.5% | 96.2% |
| Review queue | 67 | 15.5% | 61.2% |

The auto lane reached 96.2% on test against the 98% target set on validation.

Tests: 13 pytest tests (no type markers left in the data, licenses recorded, no agency or court in
two splits, the committed model reproduces the reported test accuracy, routing, the audit log stores
no text, and the Streamlit app). CI also runs ruff and scans the git history with gitleaks.

## Limits

- Contracts and court opinions come from different sources than the Federal Register documents, so
  part of their 100% accuracy comes from source style, not just content.
- Agency notices are the weak class (56%). Once their own "Notice" statements are removed, many read
  like rules, and a few (6 of 50) look like contracts.
- The classifier reads the first 6,000 characters of each document.
- Text only. Scanned PDFs need OCR first.
- No authentication in the app.

## What's next

- Add common intake types (letters, pleadings, motions) from public court records.
- Compare with a small fine-tuned transformer on the same split.

## Data and licenses

- Federal Register documents (federalregister.gov API): U.S. government works, public domain.
- Court opinions from the Caselaw Access Project (static.case.law, Federal Reporter 3d volumes
  500-600): public domain.
- Contracts from CUAD v1 by The Atticus Project (Zenodo record 4595826): CC BY 4.0.
- Each row in `data/documents.csv.gz` records its source, license and URL.


## License

Code: MIT, see [LICENSE](LICENSE). Data: see above.
