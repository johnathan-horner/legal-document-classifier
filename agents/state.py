"""
State management for the legal document processing pipeline.
"""
from typing import Dict, List, Optional, Any, TypedDict
from dataclasses import dataclass, field
from datetime import datetime
import uuid


class AgentState(TypedDict):
    """State passed between agents in the LangGraph pipeline."""

    # Document information
    document_id: str
    s3_bucket: str
    s3_key: str

    # Textract results
    extracted_text: Optional[str]
    textract_confidence: Optional[float]
    page_count: Optional[int]

    # Classification results
    document_class: Optional[str]
    classification_confidence: Optional[float]
    jurisdiction: Optional[str]

    # Clause analysis
    clause_analysis: Optional[Dict[str, Any]]
    detected_clauses: Optional[List[Dict[str, Any]]]

    # Regulatory analysis
    regulatory_analysis: Optional[Dict[str, Any]]
    compliance_gaps: Optional[List[Dict[str, Any]]]

    # Risk scoring
    risk_score: Optional[float]
    risk_breakdown: Optional[Dict[str, float]]

    # Briefing
    attorney_briefing: Optional[str]

    # Routing decision
    routing_decision: Optional[str]
    queue_priority: Optional[int]

    # Metadata
    processing_start_time: datetime
    processing_stages: Dict[str, datetime]
    errors: List[str]


@dataclass
class ClauseAnalysis:
    """Result of clause analysis."""
    clause_type: str
    text_excerpt: str
    risk_level: str  # low, medium, high
    confidence: float
    explanation: str
    regulatory_implications: List[str] = field(default_factory=list)


@dataclass
class ComplianceGap:
    """Identified compliance gap."""
    regulation_id: str
    regulation_name: str
    requirement: str
    gap_description: str
    severity: str  # low, medium, high, critical
    recommended_action: str


@dataclass
class RiskScoreBreakdown:
    """Detailed risk score breakdown."""
    classifier_confidence_score: float  # 0-1, weighted 30%
    clause_risk_score: float           # 0-1, weighted 40%
    compliance_risk_score: float       # 0-1, weighted 30%
    final_score: float                 # 0-1, composite
    risk_factors: List[str]
    mitigation_suggestions: List[str]


@dataclass
class AttorneyBriefing:
    """Attorney briefing structure."""
    summary: str
    document_classification: str
    jurisdiction: str
    key_findings: List[str]
    flagged_clauses: List[ClauseAnalysis]
    compliance_gaps: List[ComplianceGap]
    risk_assessment: RiskScoreBreakdown
    recommended_action: str
    estimated_review_time: int  # minutes
    priority_level: str


def create_initial_state(
    s3_bucket: str,
    s3_key: str,
    document_id: Optional[str] = None
) -> AgentState:
    """Create initial state for document processing."""

    if document_id is None:
        document_id = str(uuid.uuid4())

    return AgentState(
        document_id=document_id,
        s3_bucket=s3_bucket,
        s3_key=s3_key,
        extracted_text=None,
        textract_confidence=None,
        page_count=None,
        document_class=None,
        classification_confidence=None,
        jurisdiction=None,
        clause_analysis=None,
        detected_clauses=None,
        regulatory_analysis=None,
        compliance_gaps=None,
        risk_score=None,
        risk_breakdown=None,
        attorney_briefing=None,
        routing_decision=None,
        queue_priority=None,
        processing_start_time=datetime.utcnow(),
        processing_stages={},
        errors=[]
    )


def update_stage_timestamp(state: AgentState, stage_name: str) -> AgentState:
    """Update processing stage timestamp."""
    state["processing_stages"][stage_name] = datetime.utcnow()
    return state


def add_error(state: AgentState, error_message: str) -> AgentState:
    """Add error message to state."""
    state["errors"].append(f"{datetime.utcnow().isoformat()}: {error_message}")
    return state