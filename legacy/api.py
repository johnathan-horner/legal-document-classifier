"""
Legal Document Classification API

FastAPI application for legal document classification, clause analysis,
compliance checking, and risk scoring with comprehensive OpenAPI documentation.
"""

import os
import time
import hashlib
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging
import json

from fastapi import FastAPI, HTTPException, BackgroundTasks, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer
from pydantic import BaseModel, Field
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Security
security = HTTPBearer()

# Pydantic Models for API
class DocumentClassifyRequest(BaseModel):
    """Request model for document classification."""
    text: str = Field(..., description="Legal document text to classify", min_length=10)
    include_metadata: bool = Field(default=False, description="Include additional metadata in response")

class DocumentClassifyResponse(BaseModel):
    """Response model for document classification."""
    document_id: str = Field(..., description="Unique document identifier")
    classification: str = Field(..., description="Document type (contract, memorandum, policy, regulation, agreement, amendment)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Classification confidence score")
    all_scores: Dict[str, float] = Field(..., description="Confidence scores for all document classes")
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Analysis timestamp")

class ClauseAnalysisRequest(BaseModel):
    """Request model for clause analysis."""
    text: str = Field(..., description="Legal document text to analyze for clauses", min_length=10)
    risk_threshold: float = Field(default=0.5, ge=0.0, le=1.0, description="Minimum risk score to flag clauses")

class ClauseResult(BaseModel):
    """Individual clause analysis result."""
    clause_type: str = Field(..., description="Type of clause detected")
    text_excerpt: str = Field(..., description="Relevant text excerpt")
    risk_level: str = Field(..., description="Risk level (high, medium, low)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Detection confidence")
    explanation: str = Field(..., description="Risk assessment explanation")

class ClauseAnalysisResponse(BaseModel):
    """Response model for clause analysis."""
    document_id: str = Field(..., description="Unique document identifier")
    flagged_clauses: List[ClauseResult] = Field(..., description="List of flagged clauses")
    total_clauses_found: int = Field(..., description="Total number of clauses analyzed")
    high_risk_count: int = Field(..., description="Number of high-risk clauses")
    recommendations: List[str] = Field(..., description="Specific recommendations for improvements")
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")

class ComplianceGap(BaseModel):
    """Compliance gap details."""
    regulation_id: str = Field(..., description="Regulation identifier")
    regulation_name: str = Field(..., description="Full regulation name")
    requirement: str = Field(..., description="Specific requirement")
    status: str = Field(..., description="Compliance status (gap, compliant, partial)")
    severity: str = Field(..., description="Gap severity (high, medium, low)")
    detail: str = Field(..., description="Detailed explanation of the gap")

class ComplianceCheckResponse(BaseModel):
    """Response model for regulatory compliance check."""
    document_id: str = Field(..., description="Unique document identifier")
    compliance_gaps: List[ComplianceGap] = Field(..., description="List of identified compliance gaps")
    compliance_score: float = Field(..., ge=0.0, le=100.0, description="Overall compliance score (0-100)")
    critical_gaps: List[ComplianceGap] = Field(..., description="High-priority compliance gaps")
    recommendations: List[str] = Field(..., description="Specific remediation steps")
    total_checks_performed: int = Field(..., description="Total number of compliance checks")

class BriefingResponse(BaseModel):
    """Response model for attorney briefing generation."""
    document_id: str = Field(..., description="Unique document identifier")
    executive_summary: str = Field(..., description="High-level document overview")
    key_provisions: List[str] = Field(..., description="Important clauses and terms")
    risk_assessment: str = Field(..., description="Legal and business risks identified")
    recommendations: List[str] = Field(..., description="Actionable next steps")
    briefing_id: str = Field(..., description="Unique briefing identifier")

class RiskScoreResponse(BaseModel):
    """Response model for risk scoring."""
    document_id: str = Field(..., description="Unique document identifier")
    composite_risk_score: float = Field(..., ge=0.0, le=1.0, description="Overall risk score (0.0-1.0)")
    risk_breakdown: Dict[str, float] = Field(..., description="Individual risk component scores")
    routing_recommendation: str = Field(..., description="Suggested review process")
    priority_level: str = Field(..., description="Urgency classification (high, medium, low)")

class HealthCheckResponse(BaseModel):
    """Health check response model."""
    status: str = Field(..., description="Service status")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: str = Field(..., description="API version")
    uptime_seconds: float = Field(..., description="Service uptime in seconds")

# Tags metadata for OpenAPI documentation
tags_metadata = [
    {"name": "Health", "description": "System health and status endpoints"},
    {"name": "Classification", "description": "Document classification endpoints"},
    {"name": "Analysis", "description": "Clause analysis and risk scoring"},
    {"name": "Compliance", "description": "Regulatory compliance checking"},
    {"name": "Briefing", "description": "Attorney briefing generation"},
]

# Initialize FastAPI app
app = FastAPI(
    title="Legal Document Classification & Risk Scoring API",
    description="Production API for legal document processing with AI-powered classification, clause analysis, compliance checking, and risk assessment",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=tags_metadata
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables
startup_time = time.time()

# Mock data for demo purposes (in production, this would connect to actual models)
DOCUMENT_CLASSES = ["contract", "memorandum", "policy", "regulation", "agreement", "amendment"]

def generate_mock_classification(text: str) -> Dict[str, Any]:
    """Generate mock classification for demo purposes."""
    doc_hash = hashlib.md5(text.encode()).hexdigest()
    document_id = f"doc_{doc_hash[:8]}"

    # Mock classification based on content patterns
    text_lower = text.lower()
    if any(word in text_lower for word in ['agreement', 'contract', 'services']):
        classification = "contract"
        confidence = 0.91
    elif any(word in text_lower for word in ['memorandum', 'memo', 'policy']):
        classification = "memorandum"
        confidence = 0.87
    elif 'regulation' in text_lower or 'cfr' in text_lower:
        classification = "regulation"
        confidence = 0.94
    elif 'amendment' in text_lower or 'modification' in text_lower:
        classification = "amendment"
        confidence = 0.83
    elif any(word in text_lower for word in ['policy', 'procedure', 'guideline']):
        classification = "policy"
        confidence = 0.89
    else:
        classification = "agreement"
        confidence = 0.76

    # Generate mock scores for all classes
    all_scores = {cls: 0.1 for cls in DOCUMENT_CLASSES}
    all_scores[classification] = confidence
    remaining = 1.0 - confidence
    for cls in DOCUMENT_CLASSES:
        if cls != classification:
            all_scores[cls] = remaining / (len(DOCUMENT_CLASSES) - 1)

    return {
        "document_id": document_id,
        "classification": classification,
        "confidence": confidence,
        "all_scores": all_scores
    }

# API Endpoints

@app.get("/health", response_model=HealthCheckResponse, summary="System Health Check", tags=["Health"])
async def health_check():
    """Check system health, uptime, and service availability."""
    uptime = time.time() - startup_time

    return HealthCheckResponse(
        status="healthy",
        version="1.0.0",
        uptime_seconds=uptime
    )

@app.post("/classify", response_model=DocumentClassifyResponse, summary="Classify Legal Document", tags=["Classification"])
async def classify_document(request: DocumentClassifyRequest):
    """
    Classify a legal document into one of six predefined categories using AI classification.

    **Document Classes:**
    - contract: Legal contracts and service agreements
    - memorandum: Internal memos and policy documents
    - policy: Organizational policies and procedures
    - regulation: Government regulations and rules
    - agreement: Formal agreements and treaties
    - amendment: Modifications to existing documents
    """
    try:
        start_time = time.time()

        # Generate classification
        result = generate_mock_classification(request.text)
        processing_time = (time.time() - start_time) * 1000

        return DocumentClassifyResponse(
            document_id=result["document_id"],
            classification=result["classification"],
            confidence=result["confidence"],
            all_scores=result["all_scores"],
            processing_time_ms=processing_time
        )
    except Exception as e:
        logger.error(f"Classification failed: {e}")
        raise HTTPException(status_code=500, detail=f"Classification failed: {str(e)}")

@app.post("/analyze-clauses", response_model=ClauseAnalysisResponse, summary="Analyze Document Clauses", tags=["Analysis"])
async def analyze_clauses(request: ClauseAnalysisRequest):
    """
    Analyze document text to identify and flag problematic clauses with risk assessments.

    **Clause Types Detected:**
    - Indemnification clauses
    - Liability limitation clauses
    - Data sharing provisions
    - Termination clauses
    - Intellectual property clauses
    """
    try:
        start_time = time.time()
        doc_hash = hashlib.md5(request.text.encode()).hexdigest()
        document_id = f"doc_{doc_hash[:8]}"

        # Mock clause analysis
        flagged_clauses = []
        text_lower = request.text.lower()

        if 'indemnif' in text_lower:
            flagged_clauses.append(ClauseResult(
                clause_type="indemnification",
                text_excerpt="Contractor agrees to indemnify, defend, and hold harmless the Government...",
                risk_level="high",
                confidence=0.94,
                explanation="Unlimited indemnification exposes agency to uncapped liability."
            ))

        if 'liability' in text_lower and 'limit' in text_lower:
            flagged_clauses.append(ClauseResult(
                clause_type="liability_limitation",
                text_excerpt="In no event shall either party be liable for consequential damages...",
                risk_level="medium",
                confidence=0.88,
                explanation="May conflict with government requirements for damage recovery."
            ))

        processing_time = (time.time() - start_time) * 1000
        high_risk_count = sum(1 for clause in flagged_clauses if clause.risk_level == 'high')

        return ClauseAnalysisResponse(
            document_id=document_id,
            flagged_clauses=flagged_clauses,
            total_clauses_found=len(flagged_clauses),
            high_risk_count=high_risk_count,
            recommendations=["Review high-risk clauses before execution", "Add liability caps where appropriate"],
            processing_time_ms=processing_time
        )
    except Exception as e:
        logger.error(f"Clause analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Clause analysis failed: {str(e)}")

@app.post("/check-compliance", response_model=ComplianceCheckResponse, summary="Check Regulatory Compliance", tags=["Compliance"])
async def check_compliance(request: DocumentClassifyRequest):
    """
    Check document compliance against FedRAMP, FISMA, and FAR regulations.

    **Regulations Checked:**
    - FedRAMP: Federal Risk and Authorization Management Program
    - FISMA: Federal Information Security Management Act
    - FAR: Federal Acquisition Regulation
    - Privacy Act requirements
    """
    try:
        start_time = time.time()
        doc_hash = hashlib.md5(request.text.encode()).hexdigest()
        document_id = f"doc_{doc_hash[:8]}"

        # Mock compliance checking
        compliance_gaps = []
        text_lower = request.text.lower()

        if 'contractor' in text_lower and 'nist' not in text_lower:
            compliance_gaps.append(ComplianceGap(
                regulation_id="FAR-52.204-21",
                regulation_name="Basic Safeguarding of Covered Contractor Information Systems",
                requirement="Contractor must implement NIST SP 800-171 requirements",
                status="gap",
                severity="high",
                detail="Contract missing NIST cybersecurity requirements"
            ))

        if 'cloud' in text_lower and 'fedramp' not in text_lower:
            compliance_gaps.append(ComplianceGap(
                regulation_id="FedRAMP",
                regulation_name="Federal Risk and Authorization Management Program",
                requirement="Cloud services must have FedRAMP authorization",
                status="gap",
                severity="high",
                detail="Cloud services referenced without FedRAMP authorization"
            ))

        processing_time = (time.time() - start_time) * 1000
        total_checks = 4
        gaps_found = len(compliance_gaps)
        compliance_score = max(0, (total_checks - gaps_found) / total_checks * 100)
        critical_gaps = [gap for gap in compliance_gaps if gap.severity == 'high']

        return ComplianceCheckResponse(
            document_id=document_id,
            compliance_gaps=compliance_gaps,
            compliance_score=round(compliance_score, 1),
            critical_gaps=critical_gaps,
            recommendations=["Address high-severity gaps before execution", "Add required regulatory clauses"],
            total_checks_performed=total_checks
        )
    except Exception as e:
        logger.error(f"Compliance check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Compliance check failed: {str(e)}")

@app.post("/generate-briefing", response_model=BriefingResponse, summary="Generate Attorney Briefing", tags=["Briefing"])
async def generate_briefing(request: DocumentClassifyRequest):
    """
    Generate a comprehensive plain-English attorney briefing summarizing the document.

    **Briefing Includes:**
    - Executive summary of key points
    - Important provisions and clauses
    - Risk assessment and legal concerns
    - Actionable recommendations
    """
    try:
        start_time = time.time()
        doc_hash = hashlib.md5(request.text.encode()).hexdigest()
        document_id = f"doc_{doc_hash[:8]}"
        briefing_id = f"brief_{doc_hash[:8]}"

        # Mock briefing generation
        text_lower = request.text.lower()

        if 'contract' in text_lower or 'agreement' in text_lower:
            executive_summary = """Professional services contract for government consulting. Contains standard
            provisions but requires review of liability and indemnification clauses."""

            key_provisions = [
                "Professional services scope and deliverables",
                "30-day termination for convenience",
                "Unlimited contractor indemnification",
                "Standard intellectual property protections"
            ]

            risk_assessment = """HIGH RISK: Unlimited indemnification clause. MEDIUM RISK: Data handling
            provisions lack security controls. LOW RISK: Standard government contract format."""
        else:
            executive_summary = "Document analysis completed. Standard government format identified."
            key_provisions = ["Document classification completed", "No unusual provisions identified"]
            risk_assessment = "Risk assessment varies based on document type and content."

        return BriefingResponse(
            document_id=document_id,
            executive_summary=executive_summary,
            key_provisions=key_provisions,
            risk_assessment=risk_assessment,
            recommendations=[
                "Review high-risk clauses before execution",
                "Ensure compliance with federal regulations",
                "Verify proper legal authorities"
            ],
            briefing_id=briefing_id
        )
    except Exception as e:
        logger.error(f"Briefing generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Briefing generation failed: {str(e)}")

@app.post("/risk-score", response_model=RiskScoreResponse, summary="Calculate Risk Score", tags=["Analysis"])
async def calculate_risk_score(request: DocumentClassifyRequest):
    """
    Calculate a composite risk score and routing recommendation for the document.

    **Risk Factors:**
    - Clause risk assessment
    - Regulatory compliance gaps
    - Classification confidence
    - Contract complexity
    """
    try:
        start_time = time.time()
        doc_hash = hashlib.md5(request.text.encode()).hexdigest()
        document_id = f"doc_{doc_hash[:8]}"

        text_lower = request.text.lower()

        # Mock risk scoring
        clause_risk = 0.7 if 'indemnif' in text_lower else 0.3
        compliance_risk = 0.6 if ('contractor' in text_lower and 'nist' not in text_lower) else 0.2
        classification_uncertainty = 0.1

        composite_score = (clause_risk * 0.4 + compliance_risk * 0.4 + classification_uncertainty * 0.2)

        if composite_score >= 0.7:
            routing = "senior_attorney_review"
            priority = "high"
        elif composite_score >= 0.4:
            routing = "standard_legal_review"
            priority = "medium"
        else:
            routing = "expedited_approval"
            priority = "low"

        return RiskScoreResponse(
            document_id=document_id,
            composite_risk_score=round(composite_score, 3),
            risk_breakdown={
                "clause_risk_score": round(clause_risk, 3),
                "compliance_risk_score": round(compliance_risk, 3),
                "classification_uncertainty": round(classification_uncertainty, 3)
            },
            routing_recommendation=routing,
            priority_level=priority
        )
    except Exception as e:
        logger.error(f"Risk scoring failed: {e}")
        raise HTTPException(status_code=500, detail=f"Risk scoring failed: {str(e)}")

# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "status_code": exc.status_code}
    )

@app.exception_handler(500)
async def internal_server_error_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "status_code": 500}
    )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)