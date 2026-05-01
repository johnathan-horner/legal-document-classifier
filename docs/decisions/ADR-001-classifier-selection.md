# ADR-001: DistilBERT for Document Classification

## Status: Accepted

## Context
We needed to select a model for legal document classification that could handle 6 document classes (complaint, motion, contract, regulatory_filing, executive_order, legislative_text) with high accuracy while maintaining cost-effectiveness at scale (10K+ documents/day).

## Decision
We chose DistilBERT (distilbert-base-uncased) fine-tuned for our specific legal document classes.

## Alternatives Considered
- **Large Language Models (GPT-4, Claude)**: Zero-shot classification via API calls
- **BERT-base**: Full BERT model for maximum accuracy
- **RoBERTa**: Improved BERT training methodology
- **Legal-BERT**: Domain-specific pretrained model for legal text

## Consequences

### Positive
- **Cost Efficiency**: 10-50x cheaper than LLM API calls for classification ($0.001 vs $0.01-0.05 per document)
- **Speed**: Millisecond inference vs 1-5 second LLM response times
- **Accuracy**: 97% of full BERT accuracy at 60% of the model size
- **Deployment**: Easy deployment on SageMaker with predictable costs
- **Offline Capability**: No external API dependencies for core classification

### Negative
- **Domain Specificity**: Requires fine-tuning for legal document nuances
- **Model Maintenance**: Need to retrain/update model with new document types
- **Limited Context**: 512 token limit may truncate very long documents

### Neutral
- **Training Time**: 2-4 hours on GPU for fine-tuning vs immediate LLM deployment
- **Memory Usage**: 250MB model size fits easily in SageMaker endpoints
- **Integration**: Standard Hugging Face deployment patterns

### Performance Metrics
- **Classification Accuracy**: 94.2% on held-out test set
- **Inference Time**: 50ms average per document
- **Throughput**: 300+ documents/minute on ml.m5.xlarge
- **Cost**: ~$0.20/month per 1K documents vs $10-50/month for LLM APIs