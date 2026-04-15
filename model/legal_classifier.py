"""
Legal document classification model using fine-tuned DistilBERT.
Includes both document classification and key clause detection heads.
"""
import torch
import torch.nn as nn
from torch.nn import functional as F
from transformers import (
    DistilBertModel,
    DistilBertConfig,
    DistilBertTokenizer
)
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
from .config import ModelConfig


class LegalDocumentClassifier(nn.Module):
    """
    Multi-task DistilBERT model for legal document classification and clause detection.
    """

    def __init__(self, config: ModelConfig):
        super().__init__()
        self.config = config

        # Base DistilBERT model
        self.distilbert_config = DistilBertConfig.from_pretrained(
            config.model_name,
            num_labels=config.num_classes
        )
        self.distilbert = DistilBertModel.from_pretrained(
            config.model_name,
            config=self.distilbert_config
        )

        # Dropout layer
        self.dropout = nn.Dropout(config.dropout_rate)

        # Document classification head
        self.doc_classifier = nn.Linear(
            self.distilbert.config.hidden_size,
            config.num_classes
        )

        # Clause detection head (multi-label classification)
        self.clause_classifier = nn.Linear(
            self.distilbert.config.hidden_size,
            len(config.clause_classes)
        )

        # Initialize weights
        self._init_weights()

    def _init_weights(self):
        """Initialize classifier weights."""
        for module in [self.doc_classifier, self.clause_classifier]:
            module.weight.data.normal_(mean=0.0, std=0.02)
            module.bias.data.zero_()

    def forward(
        self,
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor,
        return_clause_detection: bool = True
    ) -> Dict[str, torch.Tensor]:
        """
        Forward pass through the model.

        Args:
            input_ids: Token IDs [batch_size, seq_len]
            attention_mask: Attention mask [batch_size, seq_len]
            return_clause_detection: Whether to return clause detection logits

        Returns:
            Dictionary containing:
                - doc_logits: Document classification logits [batch_size, num_classes]
                - clause_logits: Clause detection logits [batch_size, num_clause_classes]
                - hidden_states: Last hidden state [batch_size, seq_len, hidden_size]
                - pooled_output: Pooled representation [batch_size, hidden_size]
        """
        # Get DistilBERT outputs
        outputs = self.distilbert(
            input_ids=input_ids,
            attention_mask=attention_mask
        )

        # Extract hidden states and pooled output
        last_hidden_state = outputs.last_hidden_state  # [batch_size, seq_len, hidden_size]

        # Use [CLS] token representation for classification
        cls_output = last_hidden_state[:, 0]  # [batch_size, hidden_size]

        # Apply dropout
        pooled_output = self.dropout(cls_output)

        # Document classification
        doc_logits = self.doc_classifier(pooled_output)

        result = {
            "doc_logits": doc_logits,
            "hidden_states": last_hidden_state,
            "pooled_output": pooled_output
        }

        # Clause detection (optional)
        if return_clause_detection:
            clause_logits = self.clause_classifier(pooled_output)
            result["clause_logits"] = clause_logits

        return result

    def predict(
        self,
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor,
        threshold: float = 0.5
    ) -> Dict[str, Any]:
        """
        Make predictions with confidence scores and clause detection.

        Args:
            input_ids: Token IDs
            attention_mask: Attention mask
            threshold: Threshold for clause detection

        Returns:
            Dictionary with predictions and confidence scores
        """
        self.eval()
        with torch.no_grad():
            outputs = self.forward(input_ids, attention_mask)

            # Document classification
            doc_probs = F.softmax(outputs["doc_logits"], dim=-1)
            doc_confidence, doc_pred = torch.max(doc_probs, dim=-1)

            # Clause detection (multi-label)
            clause_probs = torch.sigmoid(outputs["clause_logits"])
            clause_preds = (clause_probs > threshold).float()

            return {
                "document_class": doc_pred.cpu().numpy(),
                "document_confidence": doc_confidence.cpu().numpy(),
                "document_probabilities": doc_probs.cpu().numpy(),
                "clause_predictions": clause_preds.cpu().numpy(),
                "clause_probabilities": clause_probs.cpu().numpy(),
                "clause_confidence": torch.max(clause_probs, dim=-1)[0].cpu().numpy()
            }

    def get_attention_weights(
        self,
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor
    ) -> torch.Tensor:
        """
        Extract attention weights for interpretability.

        Args:
            input_ids: Token IDs
            attention_mask: Attention mask

        Returns:
            Attention weights from last layer
        """
        self.eval()
        with torch.no_grad():
            outputs = self.distilbert(
                input_ids=input_ids,
                attention_mask=attention_mask,
                output_attentions=True
            )
            # Return attention weights from last layer
            return outputs.attentions[-1]


class LegalDocumentProcessor:
    """
    Processor for tokenizing and preparing legal documents for classification.
    """

    def __init__(self, config: ModelConfig):
        self.config = config
        self.tokenizer = DistilBertTokenizer.from_pretrained(config.model_name)

        # Add special tokens for legal domains if needed
        special_tokens = [
            "[PLAINTIFF]", "[DEFENDANT]", "[COURT]", "[STATUTE]",
            "[SECTION]", "[CLAUSE]", "[PENALTY]", "[LIABILITY]"
        ]
        self.tokenizer.add_tokens(special_tokens)

    def preprocess_text(self, text: str) -> str:
        """
        Preprocess legal document text.

        Args:
            text: Raw document text

        Returns:
            Cleaned text
        """
        # Remove excessive whitespace
        text = " ".join(text.split())

        # Standardize legal citations
        # This could be expanded with more sophisticated legal text preprocessing

        return text

    def tokenize(
        self,
        texts: List[str],
        max_length: Optional[int] = None,
        padding: str = "max_length",
        truncation: bool = True,
        return_tensors: str = "pt"
    ) -> Dict[str, torch.Tensor]:
        """
        Tokenize legal documents.

        Args:
            texts: List of document texts
            max_length: Maximum sequence length
            padding: Padding strategy
            truncation: Whether to truncate long sequences
            return_tensors: Return format

        Returns:
            Tokenized inputs
        """
        if max_length is None:
            max_length = self.config.max_length

        # Preprocess texts
        processed_texts = [self.preprocess_text(text) for text in texts]

        # Tokenize
        encoded = self.tokenizer(
            processed_texts,
            max_length=max_length,
            padding=padding,
            truncation=truncation,
            return_tensors=return_tensors
        )

        return encoded

    def decode_predictions(
        self,
        doc_predictions: np.ndarray,
        clause_predictions: np.ndarray,
        doc_confidences: np.ndarray,
        clause_confidences: np.ndarray
    ) -> List[Dict[str, Any]]:
        """
        Decode model predictions to human-readable format.

        Args:
            doc_predictions: Document class predictions
            clause_predictions: Clause detection predictions
            doc_confidences: Document confidence scores
            clause_confidences: Clause confidence scores

        Returns:
            List of decoded predictions
        """
        results = []

        for i in range(len(doc_predictions)):
            doc_class = self.config.class_names[doc_predictions[i]]

            # Get detected clauses
            detected_clauses = []
            for j, pred in enumerate(clause_predictions[i]):
                if pred == 1:
                    detected_clauses.append({
                        "clause_type": self.config.clause_classes[j],
                        "confidence": float(clause_confidences[i][j])
                    })

            results.append({
                "document_class": doc_class,
                "document_confidence": float(doc_confidences[i]),
                "detected_clauses": detected_clauses,
                "high_risk_clauses": [
                    clause for clause in detected_clauses
                    if clause["confidence"] > 0.7
                ]
            })

        return results


def create_model(config: ModelConfig) -> Tuple[LegalDocumentClassifier, LegalDocumentProcessor]:
    """
    Create model and processor instances.

    Args:
        config: Model configuration

    Returns:
        Tuple of (model, processor)
    """
    model = LegalDocumentClassifier(config)
    processor = LegalDocumentProcessor(config)

    # Resize model embeddings if special tokens were added
    model.distilbert.resize_token_embeddings(len(processor.tokenizer))

    return model, processor