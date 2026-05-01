# Model Card: Legal Document Classifier

## Model Details
- Model: DistilBERT (fine-tuned from distilbert-base-uncased)
- Framework: PyTorch + Hugging Face Transformers
- Type: Text classification (transformer, encoder-only)
- Version: 1.0.0
- Owner: Johnathan Horner, Shoot It Analytics LLC

## Intended Use
- Primary: Classify legal documents into 6 categories and detect high-risk clauses
- Users: Government legal teams requiring automated document intake and routing
- Out of scope: Not a legal advice system. Attorney review required for all flagged documents

## Training Data
- Base: Wikipedia + BookCorpus (DistilBERT pretrained)
- Fine-tuned on: Synthetic legal document dataset
- Classes: Complaint, Motion, Contract, Regulatory Filing, Executive Order, Legislative Text
- Clause types: Indemnification, Liability Limitation, Data Sharing, Termination, Non-compete, Penalty

## Evaluation Metrics
- Accuracy, Precision, Recall, F1, AUC-ROC per class
- Confusion matrix available via dashboard endpoint

## Risk Scoring
- Composite score from clause severity + regulatory gaps + document type
- <0.3: Auto-file
- 0.3-0.7: Junior attorney queue
- >0.7: Senior attorney queue

## Monitoring
- PSI drift detection
- Agent performance metrics (latency, token usage, error rate per agent)

## Ethical Considerations
- Model should not replace attorney judgment
- Override tracking measures disagreement rate between model and attorney
- Regular retraining with attorney feedback

## Compliance
- FedRAMP aligned: KMS encryption, CloudTrail logging, 7-year retention
- Access: Cognito RBAC (clerk, junior, senior, department head)
- Data: No data leaves AWS (Bedrock for LLM reasoning)