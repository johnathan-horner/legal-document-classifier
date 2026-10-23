"""
Configuration settings for the legal document classification model.
"""
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class ModelConfig:
    """Configuration for the DistilBERT legal document classifier."""

    # Model architecture
    model_name: str = "distilbert-base-uncased"
    num_classes: int = 6
    max_length: int = 512
    dropout_rate: float = 0.3

    # Document classes
    class_names: List[str] = None
    class_weights: Optional[Dict[str, float]] = None

    # Training parameters
    learning_rate: float = 2e-5
    batch_size: int = 16
    num_epochs: int = 10
    warmup_steps: int = 500
    weight_decay: float = 0.01
    gradient_clip_norm: float = 1.0

    # Clause detection head
    clause_classes: List[str] = None
    clause_max_length: int = 256

    # SageMaker specific
    instance_type: str = "ml.m5.large"
    instance_count: int = 1
    volume_size: int = 30

    def __post_init__(self):
        if self.class_names is None:
            self.class_names = [
                "complaint",
                "motion",
                "contract",
                "regulatory_filing",
                "executive_order",
                "legislative_text"
            ]

        if self.clause_classes is None:
            self.clause_classes = [
                "indemnification",
                "liability_limitation",
                "termination",
                "non_compete",
                "data_sharing",
                "penalty_provisions"
            ]

        if self.class_weights is None:
            # Balanced weights - can be adjusted based on dataset imbalance
            self.class_weights = {cls: 1.0 for cls in self.class_names}


@dataclass
class DataConfig:
    """Configuration for data processing and synthetic generation."""

    # Dataset parameters
    min_doc_length: int = 100
    max_doc_length: int = 5000
    samples_per_class: int = 200
    train_split: float = 0.8
    val_split: float = 0.1
    test_split: float = 0.1

    # Text preprocessing
    remove_special_chars: bool = True
    lowercase: bool = True
    remove_stopwords: bool = False  # Keep legal terminology

    # Augmentation
    synonym_replacement: bool = True
    random_insertion: bool = True
    random_swap: bool = True
    random_deletion: bool = False
    augmentation_ratio: float = 0.1


@dataclass
class AWSConfig:
    """AWS-specific configuration."""

    # SageMaker
    role_arn: str = ""
    bucket_name: str = ""
    prefix: str = "legal-classifier"

    # Model registry
    model_package_group_name: str = "legal-document-classifier"

    # Endpoints
    endpoint_name: str = "legal-classifier-endpoint"
    variant_name: str = "primary-variant"
    initial_instance_count: int = 1

    # Auto-scaling
    min_capacity: int = 1
    max_capacity: int = 10
    target_value: float = 70.0  # CPU utilization target

    def __post_init__(self):
        if not self.bucket_name:
            # Will be set during deployment with account ID
            self.bucket_name = f"legal-classifier-artifacts-{{}}"