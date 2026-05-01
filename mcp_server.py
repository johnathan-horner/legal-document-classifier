"""
Legal Document Classification MCP Server

FastMCP server exposing legal document classification and risk analysis functionality
through Model Context Protocol. Provides tools for document classification, clause analysis,
compliance checking, briefing generation, and risk scoring.
"""

import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import re

from fastmcp import FastMCP

# Initialize MCP server
mcp = FastMCP("Legal Document Classifier")

# Mock data for demo purposes (in production, this would connect to actual models and databases)
DOCUMENT_CLASSES = [
    "contract", "memorandum", "policy", "regulation", "agreement", "amendment"
]

MOCK_REGULATORY_DB = {
    "FAR-52.204-21": {
        "name": "Basic Safeguarding of Covered Contractor Information Systems",
        "requirement": "Contractor must implement NIST SP 800-171 safeguarding requirements",
        "category": "cybersecurity"
    },
    "FAR-52.224-2": {
        "name": "Privacy Act Notification",
        "requirement": "Privacy Act clause required when PII is collected",
        "category": "privacy"
    },
    "FISMA": {
        "name": "Federal Information Security Management Act",
        "requirement": "Security categorization and controls implementation",
        "category": "security"
    },
    "FedRAMP": {
        "name": "Federal Risk and Authorization Management Program",
        "requirement": "Cloud service security authorization required",
        "category": "cloud_security"
    }
}

@mcp.tool()
def classify_document(document_text: str) -> Dict[str, Any]:
    """
    Classify a legal document into one of six predefined classes.

    Args:
        document_text: The full text content of the document to classify

    Returns:
        Dictionary containing:
        - classification: Predicted document class
        - confidence: Model confidence (0.0-1.0)
        - all_scores: Confidence scores for all classes
        - processing_time_ms: Time taken for classification
        - document_id: Unique identifier for this analysis
    """
    try:
        # Generate document ID
        doc_hash = hashlib.md5(document_text.encode()).hexdigest()
        document_id = f"doc_{doc_hash[:8]}"

        # Mock classification based on content patterns
        text_lower = document_text.lower()

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
            "classification": classification,
            "confidence": confidence,
            "all_scores": all_scores,
            "processing_time_ms": 234.7,
            "document_id": document_id,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
def analyze_clauses(document_text: str) -> Dict[str, Any]:
    """
    Analyze document text to identify and flag problematic clauses with risk levels.

    Args:
        document_text: The full text content of the document to analyze

    Returns:
        Dictionary containing:
        - flagged_clauses: List of identified clauses with risk assessments
        - total_clauses_found: Total number of clauses analyzed
        - high_risk_count: Number of high-risk clauses
        - recommendations: Specific recommendations for clause modifications
    """
    try:
        flagged_clauses = []

        # Mock clause detection based on keywords
        text_lower = document_text.lower()

        if 'indemnif' in text_lower:
            flagged_clauses.append({
                "clause_type": "indemnification",
                "text_excerpt": "Contractor agrees to indemnify, defend, and hold harmless the Government...",
                "risk_level": "high",
                "confidence": 0.94,
                "explanation": "Unlimited indemnification exposes agency to uncapped liability. Recommend adding reasonable caps and carveouts."
            })

        if 'liability' in text_lower and 'limit' in text_lower:
            flagged_clauses.append({
                "clause_type": "liability_limitation",
                "text_excerpt": "In no event shall either party be liable for consequential damages...",
                "risk_level": "medium",
                "confidence": 0.88,
                "explanation": "Consequential damages exclusion conflicts with FAR requirements for Government access."
            })

        if 'data' in text_lower and ('shar' in text_lower or 'access' in text_lower):
            flagged_clauses.append({
                "clause_type": "data_sharing",
                "text_excerpt": "Contractor may share Government data with approved subcontractors...",
                "risk_level": "high",
                "confidence": 0.92,
                "explanation": "Data sharing clause lacks security controls and FedRAMP authorization requirements."
            })

        if 'terminat' in text_lower:
            flagged_clauses.append({
                "clause_type": "termination",
                "text_excerpt": "Government may terminate this agreement for convenience upon thirty days notice...",
                "risk_level": "low",
                "confidence": 0.85,
                "explanation": "Standard termination clause aligns with FAR requirements."
            })

        high_risk_count = sum(1 for clause in flagged_clauses if clause['risk_level'] == 'high')

        recommendations = []
        if high_risk_count > 0:
            recommendations.append("Review and modify high-risk clauses before contract execution")
        if any(clause['clause_type'] == 'indemnification' for clause in flagged_clauses):
            recommendations.append("Add liability caps to indemnification clauses")
        if any(clause['clause_type'] == 'data_sharing' for clause in flagged_clauses):
            recommendations.append("Specify security controls for data sharing provisions")

        return {
            "flagged_clauses": flagged_clauses,
            "total_clauses_found": len(flagged_clauses),
            "high_risk_count": high_risk_count,
            "recommendations": recommendations,
            "analysis_timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
def check_regulatory_compliance(document_text: str) -> Dict[str, Any]:
    """
    Check document compliance against FedRAMP, FISMA, and FAR regulations.

    Args:
        document_text: The full text content of the document to check

    Returns:
        Dictionary containing:
        - compliance_gaps: List of identified regulatory gaps
        - compliance_score: Overall compliance percentage
        - critical_gaps: High-priority compliance issues
        - recommendations: Specific remediation steps
    """
    try:
        compliance_gaps = []
        text_lower = document_text.lower()

        # Check for various compliance requirements
        if 'contractor' in text_lower and 'nist' not in text_lower:
            compliance_gaps.append({
                "regulation_id": "FAR-52.204-21",
                "regulation_name": "Basic Safeguarding of Covered Contractor Information Systems",
                "requirement": "Contractor must implement NIST SP 800-171 safeguarding requirements",
                "status": "gap",
                "severity": "high",
                "detail": "Contract does not reference NIST SP 800-171 safeguarding requirements for CUI"
            })

        if 'security' in text_lower and 'categorization' not in text_lower:
            compliance_gaps.append({
                "regulation_id": "FISMA",
                "regulation_name": "Federal Information Security Management Act",
                "requirement": "Security categorization and controls implementation",
                "status": "gap",
                "severity": "high",
                "detail": "No reference to FIPS 199 security categorization or required security controls"
            })

        if 'pii' in text_lower or 'personal' in text_lower:
            if 'privacy act' not in text_lower:
                compliance_gaps.append({
                    "regulation_id": "FAR-52.224-2",
                    "regulation_name": "Privacy Act Notification",
                    "requirement": "Privacy Act clause required when PII is collected",
                    "status": "gap",
                    "severity": "medium",
                    "detail": "Contract involves PII handling but missing Privacy Act notification clause"
                })

        if 'cloud' in text_lower and 'fedramp' not in text_lower:
            compliance_gaps.append({
                "regulation_id": "FedRAMP",
                "regulation_name": "Federal Risk and Authorization Management Program",
                "requirement": "Cloud service security authorization required",
                "status": "gap",
                "severity": "high",
                "detail": "Cloud services referenced without FedRAMP authorization requirement"
            })

        total_checks = 4
        gaps_found = len(compliance_gaps)
        compliance_score = max(0, (total_checks - gaps_found) / total_checks * 100)

        critical_gaps = [gap for gap in compliance_gaps if gap['severity'] == 'high']

        recommendations = []
        if critical_gaps:
            recommendations.append("Address high-severity compliance gaps before contract execution")
        if any(gap['regulation_id'] == 'FAR-52.204-21' for gap in compliance_gaps):
            recommendations.append("Add NIST SP 800-171 cybersecurity requirements clause")
        if any(gap['regulation_id'] == 'FISMA' for gap in compliance_gaps):
            recommendations.append("Include FISMA security categorization and control requirements")

        return {
            "compliance_gaps": compliance_gaps,
            "compliance_score": round(compliance_score, 1),
            "critical_gaps": critical_gaps,
            "recommendations": recommendations,
            "total_checks_performed": total_checks,
            "analysis_timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
def generate_briefing(document_text: str) -> Dict[str, Any]:
    """
    Generate a plain-English attorney briefing summarizing the document.

    Args:
        document_text: The full text content of the document to summarize

    Returns:
        Dictionary containing:
        - executive_summary: High-level document overview
        - key_provisions: Important clauses and terms
        - risk_assessment: Legal and business risks identified
        - recommendations: Actionable next steps
        - briefing_id: Unique identifier for this briefing
    """
    try:
        briefing_id = f"brief_{hashlib.md5(document_text.encode()).hexdigest()[:8]}"

        # Mock briefing generation based on document analysis
        text_lower = document_text.lower()

        if 'contract' in text_lower or 'agreement' in text_lower:
            executive_summary = """This professional services contract establishes terms for cybersecurity consulting
            services between the Government and a private contractor. The agreement includes standard government
            contracting provisions but contains several clauses requiring legal review."""

            key_provisions = [
                "Professional services for cybersecurity consulting",
                "30-day termination for convenience clause",
                "Unlimited contractor indemnification",
                "Data sharing provisions with subcontractors",
                "Standard intellectual property protections"
            ]

            risk_assessment = """HIGH RISK: Unlimited indemnification clause exposes the agency to uncapped liability.
            MEDIUM RISK: Data sharing provisions lack adequate security controls.
            LOW RISK: Standard termination and IP clauses align with federal requirements."""

        else:
            executive_summary = "Document analysis completed. Please see detailed findings below."
            key_provisions = ["Document classification completed", "Standard government format identified"]
            risk_assessment = "Risk assessment varies based on document type and content."

        recommendations = [
            "Review high-risk clauses before execution",
            "Ensure compliance with federal acquisition regulations",
            "Verify all security requirements are properly specified",
            "Confirm proper legal authorities and approvals"
        ]

        return {
            "executive_summary": executive_summary,
            "key_provisions": key_provisions,
            "risk_assessment": risk_assessment,
            "recommendations": recommendations,
            "briefing_id": briefing_id,
            "generated_timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
def get_risk_score(document_text: str) -> Dict[str, Any]:
    """
    Calculate a composite risk score and routing recommendation for the document.

    Args:
        document_text: The full text content of the document to score

    Returns:
        Dictionary containing:
        - composite_risk_score: Overall risk score (0.0-1.0)
        - risk_breakdown: Individual risk component scores
        - routing_recommendation: Suggested review process
        - priority_level: Urgency classification
    """
    try:
        text_lower = document_text.lower()

        # Calculate component risk scores
        classification_confidence = 0.91  # From mock classification

        # Clause risk scoring
        clause_risks = []
        if 'indemnif' in text_lower:
            clause_risks.append(0.9)  # High risk
        if 'liability' in text_lower:
            clause_risks.append(0.6)  # Medium risk
        if 'data' in text_lower and 'shar' in text_lower:
            clause_risks.append(0.8)  # High risk

        clause_risk_score = max(clause_risks) if clause_risks else 0.3

        # Compliance risk scoring
        compliance_gaps = 0
        if 'contractor' in text_lower and 'nist' not in text_lower:
            compliance_gaps += 1
        if 'security' in text_lower and 'categorization' not in text_lower:
            compliance_gaps += 1
        if 'cloud' in text_lower and 'fedramp' not in text_lower:
            compliance_gaps += 1

        compliance_risk_score = min(compliance_gaps * 0.25, 1.0)

        # Calculate composite score
        weights = {
            'clause_risk': 0.4,
            'compliance_risk': 0.4,
            'classification_uncertainty': 0.2
        }

        classification_uncertainty = 1.0 - classification_confidence

        composite_score = (
            clause_risk_score * weights['clause_risk'] +
            compliance_risk_score * weights['compliance_risk'] +
            classification_uncertainty * weights['classification_uncertainty']
        )

        # Determine routing recommendation
        if composite_score >= 0.7:
            routing = "senior_attorney_review"
            priority = "high"
        elif composite_score >= 0.4:
            routing = "standard_legal_review"
            priority = "medium"
        else:
            routing = "expedited_approval"
            priority = "low"

        return {
            "composite_risk_score": round(composite_score, 3),
            "risk_breakdown": {
                "clause_risk_score": round(clause_risk_score, 3),
                "compliance_risk_score": round(compliance_risk_score, 3),
                "classification_uncertainty": round(classification_uncertainty, 3)
            },
            "routing_recommendation": routing,
            "priority_level": priority,
            "score_timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        return {"error": str(e)}

@mcp.resource("model://classifier")
def get_classifier_info() -> str:
    """
    Get information about the DistilBERT model used for document classification.

    Returns model details including version, classes, accuracy metrics, and training information.
    """
    model_info = {
        "model_name": "DistilBERT Legal Classifier",
        "base_model": "distilbert-base-uncased",
        "version": "2.1.0",
        "num_classes": 6,
        "classes": DOCUMENT_CLASSES,
        "accuracy_metrics": {
            "overall_accuracy": 0.912,
            "weighted_f1_score": 0.908,
            "macro_f1_score": 0.894,
            "precision": 0.916,
            "recall": 0.903
        },
        "training_data": {
            "total_documents": 50000,
            "training_split": 0.8,
            "validation_split": 0.1,
            "test_split": 0.1,
            "data_sources": ["Federal contracts", "Legal documents", "Government memos"]
        },
        "model_parameters": {
            "max_sequence_length": 512,
            "batch_size": 16,
            "learning_rate": 2e-5,
            "epochs": 3
        },
        "last_updated": "2024-03-20T14:00:00Z"
    }

    return json.dumps(model_info, indent=2)

@mcp.resource("data://regulatory_requirements")
def get_regulatory_requirements() -> str:
    """
    Get the regulatory requirements database used for compliance checking.

    Returns comprehensive regulatory framework including FedRAMP, FISMA, and FAR requirements.
    """
    regulatory_data = {
        "framework_version": "2024.1",
        "last_updated": "2024-04-01T10:00:00Z",
        "regulations": MOCK_REGULATORY_DB,
        "compliance_categories": {
            "cybersecurity": {
                "description": "Information security and cyber protection requirements",
                "key_regulations": ["FAR-52.204-21", "FISMA", "NIST SP 800-171"]
            },
            "privacy": {
                "description": "Personal information protection and privacy requirements",
                "key_regulations": ["FAR-52.224-2", "Privacy Act", "FOIA"]
            },
            "cloud_security": {
                "description": "Cloud service security authorization requirements",
                "key_regulations": ["FedRAMP", "FISMA", "NIST SP 800-53"]
            },
            "acquisition": {
                "description": "Federal acquisition and contracting requirements",
                "key_regulations": ["FAR", "DFARS", "GSA regulations"]
            }
        },
        "risk_scoring_matrix": {
            "high_risk_indicators": [
                "Missing NIST cybersecurity requirements",
                "Inadequate data protection clauses",
                "Non-compliant cloud service provisions"
            ],
            "medium_risk_indicators": [
                "Missing Privacy Act notifications",
                "Incomplete security categorization",
                "Standard clause variations"
            ],
            "low_risk_indicators": [
                "Standard FAR clauses present",
                "Proper legal authorities cited",
                "Adequate termination provisions"
            ]
        }
    }

    return json.dumps(regulatory_data, indent=2)

@mcp.prompt()
def full_analysis() -> str:
    """
    Pre-built prompt for complete document analysis pipeline.

    Use this prompt to perform comprehensive legal document analysis including classification,
    clause review, compliance checking, and risk assessment.
    """
    return """You are a senior government attorney conducting a comprehensive legal document analysis.

Please perform the following complete analysis pipeline on the provided document:

**PHASE 1: DOCUMENT CLASSIFICATION**
1. Classify the document type (contract, memorandum, policy, regulation, agreement, amendment)
2. Assess classification confidence and identify any ambiguities
3. Note any unusual document characteristics or format variations

**PHASE 2: CLAUSE-BY-CLAUSE REVIEW**
1. Identify and extract all significant clauses
2. Assess risk level for each clause (high/medium/low)
3. Flag any non-standard or problematic language
4. Compare against standard government contract templates

**PHASE 3: REGULATORY COMPLIANCE CHECK**
1. Review against FedRAMP requirements (if cloud services involved)
2. Check FISMA compliance for security categorization and controls
3. Verify FAR clause compliance and proper citation
4. Identify any missing required clauses or notifications

**PHASE 4: RISK ASSESSMENT**
1. Calculate composite risk score based on clause analysis and compliance gaps
2. Identify critical issues requiring immediate attention
3. Assess business impact and legal exposure
4. Determine appropriate review routing and approval level

**PHASE 5: RECOMMENDATIONS**
1. Provide specific contract modification recommendations
2. Suggest negotiation priorities and fallback positions
3. Identify required legal clearances or approvals
4. Recommend timeline for review and execution

**DELIVERABLE FORMAT:**
- Executive summary with key findings and recommendations
- Detailed analysis with supporting rationale
- Risk matrix with mitigation strategies
- Action items with responsible parties and deadlines

Focus on protecting Government interests while enabling mission execution."""

@mcp.prompt()
def batch_review() -> str:
    """
    Pre-built prompt for batch document processing summary.

    Use this prompt to analyze multiple documents and provide aggregate insights
    for legal review efficiency.
    """
    return """You are the Chief Legal Counsel reviewing a batch of documents for processing efficiency and consistency.

Please analyze this batch of documents and provide the following assessment:

**BATCH OVERVIEW**
1. Total documents processed and document type distribution
2. Average processing time and throughput metrics
3. Overall quality and consistency of legal review
4. Common patterns or issues across multiple documents

**RISK ANALYSIS SUMMARY**
1. High-risk documents requiring immediate senior attorney review
2. Medium-risk documents suitable for standard legal review
3. Low-risk documents eligible for expedited processing
4. Consistent risk patterns that might indicate systemic issues

**COMPLIANCE PATTERNS**
1. Most frequent regulatory compliance gaps across the batch
2. Documents with critical compliance deficiencies
3. Trends in missing clauses or required notifications
4. Recommendations for template improvements

**PROCESS OPTIMIZATION**
1. Documents that could benefit from standardized templates
2. Common negotiation points that could be pre-approved
3. Workflow bottlenecks or approval delays identified
4. Training needs for contracting staff

**QUALITY ASSURANCE**
1. Consistency of risk scoring across similar document types
2. Accuracy of automated classification and flagging
3. Reviewer agreement rates on risk assessments
4. Calibration recommendations for risk thresholds

**STRATEGIC RECOMMENDATIONS**
1. Template standardization opportunities
2. Approval process streamlining recommendations
3. Risk tolerance adjustments based on mission needs
4. Technology enhancements to improve efficiency

Provide actionable insights to improve both legal protection and acquisition efficiency."""

if __name__ == "__main__":
    mcp.run()