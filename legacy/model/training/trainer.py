"""
Training pipeline for legal document classification model.
"""
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset
from torch.optim import AdamW
from torch.optim.lr_scheduler import get_linear_schedule_with_warmup
from transformers import get_linear_schedule_with_warmup
from sklearn.metrics import classification_report, confusion_matrix, f1_score
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
import logging
import wandb
from tqdm import tqdm
import json
from pathlib import Path

from ..legal_classifier import LegalDocumentClassifier, LegalDocumentProcessor
from ..config import ModelConfig


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LegalDocumentDataset(Dataset):
    """Dataset for legal document classification and clause detection."""

    def __init__(
        self,
        texts: List[str],
        doc_labels: List[int],
        clause_labels: List[List[int]],
        processor: LegalDocumentProcessor,
        max_length: int = 512
    ):
        self.texts = texts
        self.doc_labels = doc_labels
        self.clause_labels = clause_labels
        self.processor = processor
        self.max_length = max_length

    def __len__(self) -> int:
        return len(self.texts)

    def __getitem__(self, idx: int) -> Dict[str, torch.Tensor]:
        text = self.texts[idx]
        doc_label = self.doc_labels[idx]
        clause_label = self.clause_labels[idx]

        # Tokenize text
        encoded = self.processor.tokenize(
            [text],
            max_length=self.max_length,
            return_tensors="pt"
        )

        return {
            "input_ids": encoded["input_ids"].squeeze(0),
            "attention_mask": encoded["attention_mask"].squeeze(0),
            "doc_labels": torch.tensor(doc_label, dtype=torch.long),
            "clause_labels": torch.tensor(clause_label, dtype=torch.float)
        }


class LegalClassifierTrainer:
    """Trainer class for the legal document classifier."""

    def __init__(
        self,
        model: LegalDocumentClassifier,
        config: ModelConfig,
        train_dataset: LegalDocumentDataset,
        val_dataset: LegalDocumentDataset,
        test_dataset: Optional[LegalDocumentDataset] = None
    ):
        self.model = model
        self.config = config
        self.train_dataset = train_dataset
        self.val_dataset = val_dataset
        self.test_dataset = test_dataset

        # Setup device
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)

        # Create data loaders
        self.train_loader = DataLoader(
            train_dataset,
            batch_size=config.batch_size,
            shuffle=True,
            num_workers=4
        )
        self.val_loader = DataLoader(
            val_dataset,
            batch_size=config.batch_size,
            shuffle=False,
            num_workers=4
        )

        if test_dataset:
            self.test_loader = DataLoader(
                test_dataset,
                batch_size=config.batch_size,
                shuffle=False,
                num_workers=4
            )

        # Setup optimizer and scheduler
        self.optimizer = AdamW(
            self.model.parameters(),
            lr=config.learning_rate,
            weight_decay=config.weight_decay
        )

        total_steps = len(self.train_loader) * config.num_epochs
        self.scheduler = get_linear_schedule_with_warmup(
            self.optimizer,
            num_warmup_steps=config.warmup_steps,
            num_training_steps=total_steps
        )

        # Loss functions
        self.doc_criterion = nn.CrossEntropyLoss()
        self.clause_criterion = nn.BCEWithLogitsLoss()

        # Training history
        self.history = {
            "train_loss": [],
            "val_loss": [],
            "train_accuracy": [],
            "val_accuracy": [],
            "train_f1": [],
            "val_f1": []
        }

    def train_epoch(self) -> Dict[str, float]:
        """Train for one epoch."""
        self.model.train()
        total_loss = 0
        doc_correct = 0
        doc_total = 0
        all_doc_preds = []
        all_doc_labels = []

        pbar = tqdm(self.train_loader, desc="Training")
        for batch in pbar:
            # Move to device
            input_ids = batch["input_ids"].to(self.device)
            attention_mask = batch["attention_mask"].to(self.device)
            doc_labels = batch["doc_labels"].to(self.device)
            clause_labels = batch["clause_labels"].to(self.device)

            # Forward pass
            outputs = self.model(input_ids, attention_mask)

            # Calculate losses
            doc_loss = self.doc_criterion(outputs["doc_logits"], doc_labels)
            clause_loss = self.clause_criterion(outputs["clause_logits"], clause_labels)

            # Weighted combination of losses
            total_batch_loss = 0.7 * doc_loss + 0.3 * clause_loss

            # Backward pass
            self.optimizer.zero_grad()
            total_batch_loss.backward()
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), self.config.gradient_clip_norm)
            self.optimizer.step()
            self.scheduler.step()

            # Statistics
            total_loss += total_batch_loss.item()

            # Document classification accuracy
            doc_preds = torch.argmax(outputs["doc_logits"], dim=-1)
            doc_correct += (doc_preds == doc_labels).sum().item()
            doc_total += doc_labels.size(0)

            all_doc_preds.extend(doc_preds.cpu().numpy())
            all_doc_labels.extend(doc_labels.cpu().numpy())

            # Update progress bar
            pbar.set_postfix({
                "loss": total_batch_loss.item(),
                "acc": doc_correct / doc_total
            })

        # Calculate metrics
        avg_loss = total_loss / len(self.train_loader)
        accuracy = doc_correct / doc_total
        f1 = f1_score(all_doc_labels, all_doc_preds, average="weighted")

        return {
            "loss": avg_loss,
            "accuracy": accuracy,
            "f1": f1
        }

    def validate(self) -> Dict[str, float]:
        """Validate the model."""
        self.model.eval()
        total_loss = 0
        doc_correct = 0
        doc_total = 0
        all_doc_preds = []
        all_doc_labels = []
        all_clause_preds = []
        all_clause_labels = []

        with torch.no_grad():
            for batch in tqdm(self.val_loader, desc="Validation"):
                # Move to device
                input_ids = batch["input_ids"].to(self.device)
                attention_mask = batch["attention_mask"].to(self.device)
                doc_labels = batch["doc_labels"].to(self.device)
                clause_labels = batch["clause_labels"].to(self.device)

                # Forward pass
                outputs = self.model(input_ids, attention_mask)

                # Calculate losses
                doc_loss = self.doc_criterion(outputs["doc_logits"], doc_labels)
                clause_loss = self.clause_criterion(outputs["clause_logits"], clause_labels)
                total_batch_loss = 0.7 * doc_loss + 0.3 * clause_loss

                total_loss += total_batch_loss.item()

                # Document classification
                doc_preds = torch.argmax(outputs["doc_logits"], dim=-1)
                doc_correct += (doc_preds == doc_labels).sum().item()
                doc_total += doc_labels.size(0)

                all_doc_preds.extend(doc_preds.cpu().numpy())
                all_doc_labels.extend(doc_labels.cpu().numpy())

                # Clause detection
                clause_probs = torch.sigmoid(outputs["clause_logits"])
                clause_preds = (clause_probs > 0.5).float()
                all_clause_preds.extend(clause_preds.cpu().numpy())
                all_clause_labels.extend(clause_labels.cpu().numpy())

        # Calculate metrics
        avg_loss = total_loss / len(self.val_loader)
        accuracy = doc_correct / doc_total
        doc_f1 = f1_score(all_doc_labels, all_doc_preds, average="weighted")

        # Clause detection metrics
        all_clause_preds = np.array(all_clause_preds)
        all_clause_labels = np.array(all_clause_labels)
        clause_f1 = f1_score(all_clause_labels, all_clause_preds, average="macro")

        return {
            "loss": avg_loss,
            "accuracy": accuracy,
            "doc_f1": doc_f1,
            "clause_f1": clause_f1
        }

    def train(self, save_path: Optional[str] = None) -> Dict[str, Any]:
        """Train the model for specified number of epochs."""
        logger.info(f"Starting training for {self.config.num_epochs} epochs")

        best_val_f1 = 0
        for epoch in range(self.config.num_epochs):
            logger.info(f"Epoch {epoch + 1}/{self.config.num_epochs}")

            # Train
            train_metrics = self.train_epoch()
            self.history["train_loss"].append(train_metrics["loss"])
            self.history["train_accuracy"].append(train_metrics["accuracy"])
            self.history["train_f1"].append(train_metrics["f1"])

            # Validate
            val_metrics = self.validate()
            self.history["val_loss"].append(val_metrics["loss"])
            self.history["val_accuracy"].append(val_metrics["accuracy"])
            self.history["val_f1"].append(val_metrics["doc_f1"])

            logger.info(
                f"Train - Loss: {train_metrics['loss']:.4f}, "
                f"Acc: {train_metrics['accuracy']:.4f}, "
                f"F1: {train_metrics['f1']:.4f}"
            )
            logger.info(
                f"Val - Loss: {val_metrics['loss']:.4f}, "
                f"Acc: {val_metrics['accuracy']:.4f}, "
                f"Doc F1: {val_metrics['doc_f1']:.4f}, "
                f"Clause F1: {val_metrics['clause_f1']:.4f}"
            )

            # Save best model
            if val_metrics["doc_f1"] > best_val_f1:
                best_val_f1 = val_metrics["doc_f1"]
                if save_path:
                    self.save_model(save_path)

            # Log to wandb if available
            if wandb.run is not None:
                wandb.log({
                    "epoch": epoch,
                    "train_loss": train_metrics["loss"],
                    "train_accuracy": train_metrics["accuracy"],
                    "train_f1": train_metrics["f1"],
                    "val_loss": val_metrics["loss"],
                    "val_accuracy": val_metrics["accuracy"],
                    "val_doc_f1": val_metrics["doc_f1"],
                    "val_clause_f1": val_metrics["clause_f1"]
                })

        return self.history

    def evaluate(self) -> Dict[str, Any]:
        """Evaluate model on test set."""
        if not self.test_dataset:
            raise ValueError("No test dataset provided")

        self.model.eval()
        all_doc_preds = []
        all_doc_labels = []
        all_clause_preds = []
        all_clause_labels = []

        with torch.no_grad():
            for batch in tqdm(self.test_loader, desc="Testing"):
                input_ids = batch["input_ids"].to(self.device)
                attention_mask = batch["attention_mask"].to(self.device)
                doc_labels = batch["doc_labels"].to(self.device)
                clause_labels = batch["clause_labels"].to(self.device)

                outputs = self.model(input_ids, attention_mask)

                # Document predictions
                doc_preds = torch.argmax(outputs["doc_logits"], dim=-1)
                all_doc_preds.extend(doc_preds.cpu().numpy())
                all_doc_labels.extend(doc_labels.cpu().numpy())

                # Clause predictions
                clause_probs = torch.sigmoid(outputs["clause_logits"])
                clause_preds = (clause_probs > 0.5).float()
                all_clause_preds.extend(clause_preds.cpu().numpy())
                all_clause_labels.extend(clause_labels.cpu().numpy())

        # Generate detailed reports
        doc_report = classification_report(
            all_doc_labels, all_doc_preds,
            target_names=self.config.class_names,
            output_dict=True
        )

        doc_confusion = confusion_matrix(all_doc_labels, all_doc_preds)

        # Clause detection metrics
        all_clause_preds = np.array(all_clause_preds)
        all_clause_labels = np.array(all_clause_labels)

        clause_report = classification_report(
            all_clause_labels, all_clause_preds,
            target_names=self.config.clause_classes,
            output_dict=True
        )

        return {
            "document_classification": {
                "report": doc_report,
                "confusion_matrix": doc_confusion.tolist(),
                "accuracy": doc_report["accuracy"],
                "f1_macro": doc_report["macro avg"]["f1-score"],
                "f1_weighted": doc_report["weighted avg"]["f1-score"]
            },
            "clause_detection": {
                "report": clause_report,
                "f1_macro": clause_report["macro avg"]["f1-score"],
                "f1_weighted": clause_report["weighted avg"]["f1-score"]
            }
        }

    def save_model(self, save_path: str):
        """Save model checkpoint."""
        save_path = Path(save_path)
        save_path.mkdir(parents=True, exist_ok=True)

        # Save model state
        torch.save({
            "model_state_dict": self.model.state_dict(),
            "config": self.config.__dict__,
            "history": self.history
        }, save_path / "model.pth")

        # Save config
        with open(save_path / "config.json", "w") as f:
            json.dump(self.config.__dict__, f, indent=2)

        logger.info(f"Model saved to {save_path}")

    @classmethod
    def load_model(
        cls,
        load_path: str,
        device: Optional[torch.device] = None
    ) -> Tuple[LegalDocumentClassifier, ModelConfig]:
        """Load model from checkpoint."""
        load_path = Path(load_path)

        # Load config
        with open(load_path / "config.json", "r") as f:
            config_dict = json.load(f)

        config = ModelConfig(**config_dict)

        # Create model
        model = LegalDocumentClassifier(config)

        # Load weights
        checkpoint = torch.load(load_path / "model.pth", map_location=device or "cpu")
        model.load_state_dict(checkpoint["model_state_dict"])

        return model, config