"""
Legal Document Classification & Risk Scoring System - Streamlit Demo Frontend
Production-grade demo interface with mock data mode for portfolio demonstrations.
"""
import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
import time
from datetime import datetime, timedelta
import json
from typing import Dict, List, Any, Optional
from fpdf import FPDF
import base64

# Page configuration
st.set_page_config(
    page_title="Legal Document Classification & Risk Scoring",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

# Mock data for demo mode
MOCK_RESPONSES = {
    "analyze_contract": {
        "document_id": "doc_12345",
        "status": "completed",
        "processing_time": 42.3,
        "document_class": "contract",
        "classification_confidence": 0.91,
        "jurisdiction": "Federal",
        "extracted_text": "PROFESSIONAL SERVICES CONTRACT\n\nThis Agreement is entered into between the United States Government, acting through the General Services Administration (GSA), and Contractor for the provision of cybersecurity consulting services...",
        "detected_clauses": [
            {
                "clause_type": "indemnification",
                "text_excerpt": "Contractor agrees to indemnify, defend, and hold harmless the Government from and against any and all claims, damages, losses, costs, and expenses",
                "risk_level": "high",
                "confidence": 0.94,
                "explanation": "Unlimited indemnification with no cap exposes the agency to uncapped liability. Recommend adding reasonable caps and carveouts for Government negligence."
            },
            {
                "clause_type": "liability_limitation",
                "text_excerpt": "In no event shall either party be liable for any indirect, incidental, special, consequential, or punitive damages",
                "risk_level": "medium",
                "confidence": 0.88,
                "explanation": "Consequential damages exclusion is standard but conflicts with FAR 52.212-4 which may require Government access to such damages."
            },
            {
                "clause_type": "data_sharing",
                "text_excerpt": "Contractor may share Government data with approved subcontractors for performance of work",
                "risk_level": "high",
                "confidence": 0.92,
                "explanation": "Allows subcontractor access to PII without specifying security controls or requiring FedRAMP authorization."
            },
            {
                "clause_type": "termination",
                "text_excerpt": "Government may terminate this agreement for convenience upon thirty (30) days written notice",
                "risk_level": "low",
                "confidence": 0.85,
                "explanation": "Standard 30-day termination for convenience clause aligns with FAR requirements."
            }
        ],
        "compliance_gaps": [
            {
                "regulation_id": "FAR-52.204-21",
                "regulation_name": "Basic Safeguarding of Covered Contractor Information Systems",
                "requirement": "Contractor must implement basic safeguarding requirements",
                "status": "gap",
                "detail": "Contract does not reference NIST SP 800-171 safeguarding requirements for CUI"
            },
            {
                "regulation_id": "FISMA",
                "regulation_name": "Federal Information Security Management Act",
                "requirement": "Security categorization and controls implementation",
                "status": "gap",
                "detail": "No reference to FIPS 199 security categorization or required security controls"
            },
            {
                "regulation_id": "FAR-52.224-2",
                "regulation_name": "Privacy Act Notification",
                "requirement": "Privacy Act clause required when PII is collected",
                "status": "gap",
                "detail": "Contract involves PII handling but missing Privacy Act notification clause"
            }
        ],
        "risk_score": 0.74,
        "risk_breakdown": {
            "classifier_confidence_score": 0.91,
            "clause_risk_score": 0.75,
            "compliance_risk_score": 0.68,
            "final_score": 0.74
        },
        "routing_decision": "senior_attorney_review",
        "queue_priority": 1,
        "attorney_briefing": "EXECUTIVE SUMMARY: High-risk government contract requiring senior attorney review before execution. Classification: Professional Services Contract (91% confidence), Federal jurisdiction. KEY FINDINGS: Four significant clauses identified, with two high-risk provisions requiring attention. The unlimited indemnification clause (Clause 1) exposes the Government to uncapped liability and should include reasonable caps and carveouts for Government negligence. The data sharing provision (Clause 3) allows subcontractor PII access without adequate security controls or FedRAMP requirements. COMPLIANCE GAPS: Three critical regulatory requirements missing: NIST SP 800-171 safeguarding (FAR 52.204-21), FISMA security categorization, and Privacy Act notification (FAR 52.224-2). RECOMMENDATION: Do not execute without addressing high-risk clauses and compliance gaps. Estimated review time: 2-3 hours. Priority: HIGH due to PII handling and unlimited liability exposure."
    },
    "attorney_queue": [
        {
            "document_id": "doc_001",
            "document_type": "contract",
            "risk_score": 0.82,
            "classification": "Professional Services Contract",
            "jurisdiction": "Federal",
            "timestamp": "2024-04-14T10:30:00Z",
            "status": "pending_review",
            "priority": 1
        },
        {
            "document_id": "doc_002",
            "document_type": "contract",
            "risk_score": 0.67,
            "classification": "Software License Agreement",
            "jurisdiction": "California",
            "timestamp": "2024-04-14T09:15:00Z",
            "status": "pending_review",
            "priority": 2
        },
        {
            "document_id": "doc_003",
            "document_type": "regulatory_filing",
            "risk_score": 0.43,
            "classification": "SEC Form 10-K",
            "jurisdiction": "Federal",
            "timestamp": "2024-04-14T08:45:00Z",
            "status": "in_review",
            "priority": 3
        },
        {
            "document_id": "doc_004",
            "document_type": "motion",
            "risk_score": 0.25,
            "classification": "Motion to Dismiss",
            "jurisdiction": "Delaware",
            "timestamp": "2024-04-14T08:20:00Z",
            "status": "pending_review",
            "priority": 4
        },
        {
            "document_id": "doc_005",
            "document_type": "complaint",
            "risk_score": 0.38,
            "classification": "Civil Complaint",
            "jurisdiction": "New York",
            "timestamp": "2024-04-14T07:55:00Z",
            "status": "pending_review",
            "priority": 5
        },
        {
            "document_id": "doc_006",
            "document_type": "contract",
            "risk_score": 0.59,
            "classification": "Employment Agreement",
            "jurisdiction": "Texas",
            "timestamp": "2024-04-14T07:30:00Z",
            "status": "pending_review",
            "priority": 6
        },
        {
            "document_id": "doc_007",
            "document_type": "executive_order",
            "risk_score": 0.19,
            "classification": "Executive Order",
            "jurisdiction": "Federal",
            "timestamp": "2024-04-14T07:10:00Z",
            "status": "completed",
            "priority": 7
        },
        {
            "document_id": "doc_008",
            "document_type": "regulatory_filing",
            "risk_score": 0.52,
            "classification": "FINRA Filing",
            "jurisdiction": "Federal",
            "timestamp": "2024-04-14T06:45:00Z",
            "status": "pending_review",
            "priority": 8
        }
    ],
    "batch_results": [
        {"filename": "contract_001.pdf", "classification": "Software License", "risk_score": 0.34, "routing": "Junior Attorney"},
        {"filename": "motion_dismiss.pdf", "classification": "Motion to Dismiss", "risk_score": 0.22, "routing": "Auto-Filed"},
        {"filename": "sec_filing.pdf", "classification": "SEC Form 10-Q", "risk_score": 0.48, "routing": "Junior Attorney"},
        {"filename": "employment_agr.pdf", "classification": "Employment Agreement", "risk_score": 0.71, "routing": "Senior Attorney"},
        {"filename": "regulatory_doc.pdf", "classification": "Regulatory Filing", "risk_score": 0.29, "routing": "Auto-Filed"}
    ],
    "dashboard_metrics": {
        "total_documents": 3412,
        "avg_risk_score": 0.41,
        "override_rate": 8.2,
        "avg_review_time": 12.3
    },
    "classification_distribution": {
        "contract": 1245,
        "motion": 867,
        "complaint": 623,
        "regulatory_filing": 421,
        "executive_order": 156,
        "legislative_text": 100
    },
    "risk_distribution": {
        "low": 2156,
        "medium": 987,
        "high": 269
    },
    "compliance_gaps": {
        "FAR 52.204-21": 34,
        "FISMA": 28,
        "FAR 52.224-2": 22,
        "SOX 404": 18,
        "GDPR": 15,
        "CCPA": 12
    },
    "agent_performance": {
        "clause_analysis": {"avg_latency": 3.2, "token_usage": 2150, "error_rate": 1.2},
        "regulatory_crossref": {"avg_latency": 2.8, "token_usage": 1890, "error_rate": 0.8},
        "briefing_generation": {"avg_latency": 4.1, "token_usage": 3200, "error_rate": 0.5}
    },
    "compliance_status": {
        "fedramp_readiness": 85,
        "kms_encryption": True,
        "cloudtrail_enabled": True,
        "retention_policy_years": 7
    }
}

def load_css():
    """Load custom CSS for styling."""
    st.markdown("""
    <style>
    .risk-high { color: #ff4b4b; font-weight: bold; }
    .risk-medium { color: #ff8c00; font-weight: bold; }
    .risk-low { color: #00c851; font-weight: bold; }
    .routing-senior { color: #ff4b4b; font-weight: bold; }
    .routing-junior { color: #ff8c00; font-weight: bold; }
    .routing-auto { color: #00c851; font-weight: bold; }
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
    }
    .briefing-card {
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #0066cc;
    }
    </style>
    """, unsafe_allow_html=True)

def create_sidebar():
    """Create the sidebar with project info and controls."""
    with st.sidebar:
        st.title("⚖️ Legal Doc AI")

        # Demo Mode Toggle
        demo_mode = st.toggle("🎭 Demo Mode", value=True, help="Use mock data for demonstration")

        st.markdown("---")

        # Project Description
        st.markdown("""
        **Production-grade legal document classification and compliance risk scoring system**

        Uses PyTorch (DistilBERT), LangGraph multi-agent pipeline, Amazon Bedrock (Claude), Amazon Textract, and full AWS serverless architecture with FedRAMP-aware government compliance.
        """)

        # Architecture Diagram
        if os.path.exists("docs/Legal_Doc_Classification_AWS_Architecture.png"):
            st.image("docs/Legal_Doc_Classification_AWS_Architecture.png", caption="AWS Architecture")

        st.markdown("---")

        # Tech Stack Badges
        st.markdown("**Tech Stack:**")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("![PyTorch](https://img.shields.io/badge/PyTorch-EE4C2C?style=flat&logo=pytorch&logoColor=white)")
            st.markdown("![LangChain](https://img.shields.io/badge/LangChain-121212?style=flat)")
            st.markdown("![AWS](https://img.shields.io/badge/AWS-FF9900?style=flat&logo=amazonaws&logoColor=white)")
        with col2:
            st.markdown("![LangGraph](https://img.shields.io/badge/LangGraph-00D4AA?style=flat)")
            st.markdown("![Bedrock](https://img.shields.io/badge/Bedrock-FF9900?style=flat)")
            st.markdown("![Textract](https://img.shields.io/badge/Textract-FF9900?style=flat)")

        st.markdown("---")

        # Multi-Agent Pipeline
        with st.expander("🔄 Multi-Agent Pipeline"):
            st.markdown("""
            **LangGraph Workflow:**
            1. Extract Text (Textract)
            2. Classify Document (DistilBERT)
            3. **Parallel Agents:**
               - Clause Analysis (Agent 1)
               - Regulatory CrossRef (Agent 2)
            4. Risk Scoring (Composite)
            5. Generate Briefing (Agent 3)
            6. Route to Attorney

            *Agents 1 & 2 run in parallel for optimal performance*
            """)

        # Compliance Note
        st.info("🔒 FedRAMP-aware design with KMS encryption, CloudTrail auditing, and RBAC")

        # GitHub Link
        st.markdown("---")
        st.markdown("[📚 GitHub Repository](https://github.com/johnathan-horner/legal-document-classifier)")

        # Footer
        st.markdown("---")
        st.caption("Built by **Johnathan Horner**")

    return demo_mode

def call_api(endpoint: str, method: str = "GET", data: Any = None, demo_mode: bool = True) -> Dict[str, Any]:
    """Make API call or return mock data in demo mode."""
    if demo_mode:
        # Return mock responses
        if endpoint == "/analyze" and method == "POST":
            return MOCK_RESPONSES["analyze_contract"]
        elif endpoint == "/queue/senior" or endpoint == "/queue/junior":
            return {"documents": MOCK_RESPONSES["attorney_queue"]}
        elif endpoint == "/batch" and method == "POST":
            return {"results": MOCK_RESPONSES["batch_results"]}
        elif endpoint == "/dashboard/metrics":
            return MOCK_RESPONSES["dashboard_metrics"]
        elif endpoint == "/dashboard/classification-distribution":
            return MOCK_RESPONSES["classification_distribution"]
        elif endpoint == "/dashboard/risk-distribution":
            return MOCK_RESPONSES["risk_distribution"]
        elif endpoint == "/dashboard/compliance-gaps":
            return MOCK_RESPONSES["compliance_gaps"]
        elif endpoint == "/dashboard/agent-performance":
            return MOCK_RESPONSES["agent_performance"]
        elif endpoint == "/dashboard/compliance-status":
            return MOCK_RESPONSES["compliance_status"]
        else:
            return {"status": "success", "message": "Demo mode response"}

    try:
        url = f"{API_BASE_URL}{endpoint}"
        if method == "GET":
            response = requests.get(url, timeout=30)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=30)
        elif method == "PUT":
            response = requests.put(url, json=data, timeout=30)

        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API Error: {str(e)}")
        return {"error": str(e)}

def create_risk_gauge(risk_score: float) -> go.Figure:
    """Create a risk score gauge chart."""
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=risk_score,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Risk Score"},
        delta={'reference': 0.5},
        gauge={
            'axis': {'range': [None, 1]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, 0.3], 'color': "lightgreen"},
                {'range': [0.3, 0.7], 'color': "yellow"},
                {'range': [0.7, 1], 'color': "lightcoral"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 0.7
            }
        }
    ))
    fig.update_layout(height=300)
    return fig

def create_briefing_pdf(briefing_text: str, document_id: str) -> bytes:
    """Create PDF from briefing text."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, 'Legal Document Analysis Briefing', ln=True, align='C')
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 10, f'Document ID: {document_id}', ln=True)
    pdf.cell(0, 10, f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', ln=True)
    pdf.ln(10)
    pdf.set_font('Arial', '', 12)

    # Split text into lines and add to PDF
    lines = briefing_text.split('. ')
    for line in lines:
        if line.strip():
            pdf.multi_cell(0, 6, line.strip() + '.', align='L')
            pdf.ln(2)

    return pdf.output(dest='S').encode('latin-1')

def tab_analyze_document(demo_mode: bool):
    """Tab 1: Document Analysis."""
    st.header("📄 Analyze Document")

    col1, col2 = st.columns([2, 1])

    with col1:
        # File uploader
        uploaded_file = st.file_uploader(
            "Upload legal document",
            type=['pdf', 'txt'],
            help="Upload a PDF or text file for analysis"
        )

    with col2:
        # Demo mode button
        if st.button("🎯 Demo Mode", type="secondary"):
            uploaded_file = "demo_contract.txt"  # Trigger demo

    if uploaded_file:
        if uploaded_file == "demo_contract.txt":
            # Demo mode
            st.success("📁 Loading sample government contract...")
            file_content = "Sample Government Professional Services Contract (Demo)"
        else:
            # Real file upload
            file_content = str(uploaded_file.read(), encoding='utf-8') if uploaded_file.type == 'text/plain' else f"PDF file: {uploaded_file.name}"

        # Processing pipeline with status updates
        with st.container():
            st.subheader("🔄 Processing Pipeline")

            # Step 1: Text Extraction
            with st.status("Step 1: Extracting text (Amazon Textract)", expanded=True) as status1:
                time.sleep(0.5)  # Simulate processing
                response = call_api("/analyze", "POST", {"file_content": file_content}, demo_mode)

                with st.expander("📝 Extracted Text Preview"):
                    st.text_area("", response.get("extracted_text", "")[:500] + "...", height=100, disabled=True)

                status1.update(label="✅ Text extraction completed", state="complete")

            # Step 2: Classification
            with st.status("Step 2: Classifying document (DistilBERT)", expanded=True) as status2:
                time.sleep(0.3)

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Classification", response.get("document_class", "contract").title())
                with col2:
                    confidence = response.get("classification_confidence", 0.91)
                    st.metric("Confidence", f"{confidence:.2%}")
                with col3:
                    st.metric("Jurisdiction", response.get("jurisdiction", "Federal"))

                status2.update(label="✅ Document classification completed", state="complete")

            # Step 3: Clause Analysis
            with st.status("Step 3: Analyzing clauses (LangGraph Agent 1)", expanded=True) as status3:
                time.sleep(0.8)

                clauses = response.get("detected_clauses", [])
                if clauses:
                    clause_df = pd.DataFrame([
                        {
                            "Clause Type": clause["clause_type"].replace("_", " ").title(),
                            "Risk Level": clause["risk_level"],
                            "Confidence": f"{clause['confidence']:.1%}",
                            "Text Excerpt": clause["text_excerpt"][:100] + "..." if len(clause["text_excerpt"]) > 100 else clause["text_excerpt"],
                            "Explanation": clause["explanation"]
                        }
                        for clause in clauses
                    ])

                    # Color code risk levels
                    def color_risk(val):
                        if val == "high":
                            return "background-color: #ffebee; color: #d32f2f"
                        elif val == "medium":
                            return "background-color: #fff3e0; color: #f57c00"
                        else:
                            return "background-color: #e8f5e8; color: #388e3c"

                    styled_df = clause_df.style.applymap(color_risk, subset=['Risk Level'])
                    st.dataframe(styled_df, use_container_width=True)

                status3.update(label="✅ Clause analysis completed", state="complete")

            # Step 4: Regulatory Cross-reference
            with st.status("Step 4: Cross-referencing regulations (LangGraph Agent 2)", expanded=True) as status4:
                time.sleep(0.6)

                gaps = response.get("compliance_gaps", [])
                if gaps:
                    gap_df = pd.DataFrame([
                        {
                            "Regulation": gap["regulation_id"],
                            "Requirement": gap["requirement"][:80] + "..." if len(gap["requirement"]) > 80 else gap["requirement"],
                            "Status": "❌ Gap" if gap["status"] == "gap" else "✅ Met",
                            "Detail": gap["detail"][:100] + "..." if len(gap["detail"]) > 100 else gap["detail"]
                        }
                        for gap in gaps
                    ])
                    st.dataframe(gap_df, use_container_width=True)

                status4.update(label="✅ Regulatory cross-reference completed", state="complete")

            # Step 5: Briefing Generation
            with st.status("Step 5: Generating briefing (LangGraph Agent 3)", expanded=True) as status5:
                time.sleep(0.4)

                briefing = response.get("attorney_briefing", "")
                if briefing:
                    st.markdown(f"""
                    <div class="briefing-card">
                        <h4>📋 Attorney Briefing</h4>
                        <p>{briefing}</p>
                    </div>
                    """, unsafe_allow_html=True)

                status5.update(label="✅ Briefing generation completed", state="complete")

        # Final Results Panel
        st.subheader("📊 Analysis Results")

        col1, col2, col3 = st.columns([2, 2, 1])

        with col1:
            # Risk Score Gauge
            risk_score = response.get("risk_score", 0.74)
            fig = create_risk_gauge(risk_score)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            # Routing Decision
            routing = response.get("routing_decision", "senior_attorney_review")
            routing_map = {
                "auto_file": ("🗂️ Auto-Filed", "success"),
                "junior_attorney_review": ("👨‍💼 Junior Attorney", "warning"),
                "senior_attorney_review": ("👩‍💼 Senior Attorney", "error"),
                "department_head": ("👑 Department Head", "error")
            }

            route_label, route_type = routing_map.get(routing, ("Unknown", "info"))

            st.metric("Routing Decision", route_label)

            if routing == "senior_attorney_review":
                st.error("🚨 High Priority Review Required")
            elif routing == "junior_attorney_review":
                st.warning("⚠️ Standard Review Required")
            else:
                st.success("✅ Low Risk - Auto Processing")

        with col3:
            # Download PDF
            if st.button("📄 Download Briefing PDF"):
                pdf_content = create_briefing_pdf(briefing, response.get("document_id", "doc_123"))
                st.download_button(
                    label="Download PDF",
                    data=pdf_content,
                    file_name=f"briefing_{response.get('document_id', 'doc_123')}.pdf",
                    mime="application/pdf"
                )

def tab_attorney_queue(demo_mode: bool):
    """Tab 2: Attorney Queue."""
    st.header("👨‍💼 Attorney Queue")

    # Role selector
    role = st.selectbox(
        "Select Role (simulates Cognito RBAC)",
        ["Junior Attorney", "Senior Attorney", "Department Head"],
        index=1
    )

    # Get queue data based on role
    endpoint_map = {
        "Junior Attorney": "/queue/junior",
        "Senior Attorney": "/queue/senior",
        "Department Head": "/queue/department_head"
    }

    queue_response = call_api(endpoint_map[role], demo_mode=demo_mode)
    documents = queue_response.get("documents", [])

    if documents:
        # Filter documents based on role (in real implementation, this would be done by backend)
        if role == "Junior Attorney":
            documents = [doc for doc in documents if doc["risk_score"] < 0.7]
        elif role == "Senior Attorney":
            documents = [doc for doc in documents if doc["risk_score"] >= 0.3]

        # Create DataFrame
        df = pd.DataFrame([
            {
                "Document ID": doc["document_id"],
                "Type": doc["document_type"].title(),
                "Classification": doc["classification"],
                "Risk Score": f"{doc['risk_score']:.2f}",
                "Jurisdiction": doc["jurisdiction"],
                "Timestamp": doc["timestamp"][:19].replace("T", " "),
                "Status": doc["status"].replace("_", " ").title(),
                "Priority": doc["priority"]
            }
            for doc in documents
        ])

        # Display queue
        st.dataframe(df, use_container_width=True)

        # Document detail expander
        selected_doc = st.selectbox("Select document for details:", df["Document ID"].tolist())

        if selected_doc:
            doc_data = next(doc for doc in documents if doc["document_id"] == selected_doc)

            with st.expander(f"📄 Document Details: {selected_doc}", expanded=True):
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric("Risk Score", f"{doc_data['risk_score']:.2f}")
                with col2:
                    st.metric("Priority", doc_data["priority"])
                with col3:
                    st.metric("Status", doc_data["status"].replace("_", " ").title())

                # Mock briefing for selected document
                st.markdown("**📋 Attorney Briefing:**")
                st.text_area("", "Standard contract analysis completed. No high-risk clauses identified. Recommend routine processing through junior attorney queue.", height=100, disabled=True)

                # Action buttons
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button("✅ Confirm Classification", key=f"confirm_{selected_doc}"):
                        call_api(f"/feedback/{selected_doc}", "POST", {"action": "confirm"}, demo_mode)
                        st.success("Classification confirmed")

                with col2:
                    new_class = st.selectbox("Override Classification:",
                                           ["contract", "motion", "complaint", "regulatory_filing"],
                                           key=f"override_{selected_doc}")
                    if st.button("🔄 Override", key=f"override_btn_{selected_doc}"):
                        call_api(f"/feedback/{selected_doc}", "POST", {"action": "override", "new_classification": new_class}, demo_mode)
                        st.success(f"Classification overridden to {new_class}")

                with col3:
                    if st.button("📋 Mark Reviewed", key=f"reviewed_{selected_doc}"):
                        call_api(f"/feedback/{selected_doc}", "POST", {"action": "reviewed"}, demo_mode)
                        st.success("Document marked as reviewed")

    else:
        st.info(f"No documents in {role.lower()} queue.")

def tab_batch_processing(demo_mode: bool):
    """Tab 3: Batch Processing."""
    st.header("📁 Batch Processing")

    # Multi-file uploader
    uploaded_files = st.file_uploader(
        "Upload multiple documents for batch processing",
        type=['pdf', 'txt'],
        accept_multiple_files=True,
        help="Select multiple files to process simultaneously"
    )

    if uploaded_files or st.button("🎯 Demo Batch"):
        if st.button("🔄 Process All", type="primary"):
            # Progress bar
            progress_bar = st.progress(0)
            status_text = st.empty()

            total_files = len(uploaded_files) if uploaded_files else 5

            for i in range(total_files):
                progress = (i + 1) / total_files
                progress_bar.progress(progress)
                status_text.text(f"Processing file {i+1} of {total_files}...")
                time.sleep(0.5)  # Simulate processing time

            # Get batch results
            batch_response = call_api("/batch", "POST", {"files": [f.name for f in uploaded_files] if uploaded_files else []}, demo_mode)
            results = batch_response.get("results", [])

            status_text.text("✅ Batch processing completed!")

            # Results table
            if results:
                st.subheader("📊 Batch Results")

                results_df = pd.DataFrame(results)

                # Color code routing decisions
                def color_routing(val):
                    if "Senior" in val:
                        return "background-color: #ffebee; color: #d32f2f"
                    elif "Junior" in val:
                        return "background-color: #fff3e0; color: #f57c00"
                    else:
                        return "background-color: #e8f5e8; color: #388e3c"

                styled_df = results_df.style.applymap(color_routing, subset=['routing'])
                st.dataframe(styled_df, use_container_width=True)

                # Summary statistics
                st.subheader("📈 Summary Statistics")

                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.metric("Total Processed", len(results))

                with col2:
                    avg_risk = sum(r["risk_score"] for r in results) / len(results)
                    st.metric("Avg Risk Score", f"{avg_risk:.2f}")

                with col3:
                    high_risk = sum(1 for r in results if r["risk_score"] > 0.7)
                    st.metric("High Risk", high_risk)

                with col4:
                    auto_filed = sum(1 for r in results if "Auto" in r["routing"])
                    st.metric("Auto-Filed", auto_filed)

                # Risk distribution chart
                risk_scores = [r["risk_score"] for r in results]
                fig = px.histogram(x=risk_scores, bins=10, title="Risk Score Distribution")
                fig.update_xaxis(title="Risk Score")
                fig.update_yaxis(title="Count")
                st.plotly_chart(fig, use_container_width=True)

    else:
        st.info("Upload files or use Demo Batch to begin processing.")

@st.cache_data(ttl=60)
def get_dashboard_data(demo_mode: bool):
    """Get dashboard data with caching."""
    return {
        "metrics": call_api("/dashboard/metrics", demo_mode=demo_mode),
        "classification_dist": call_api("/dashboard/classification-distribution", demo_mode=demo_mode),
        "risk_dist": call_api("/dashboard/risk-distribution", demo_mode=demo_mode),
        "compliance_gaps": call_api("/dashboard/compliance-gaps", demo_mode=demo_mode),
        "agent_performance": call_api("/dashboard/agent-performance", demo_mode=demo_mode),
        "compliance_status": call_api("/dashboard/compliance-status", demo_mode=demo_mode)
    }

def tab_dashboard(demo_mode: bool):
    """Tab 4: Dashboard."""
    st.header("📊 System Dashboard")

    # Get dashboard data
    data = get_dashboard_data(demo_mode)

    # Row 1: Metric Cards
    st.subheader("📈 Key Metrics")
    col1, col2, col3, col4 = st.columns(4)

    metrics = data["metrics"]

    with col1:
        st.metric("Documents Processed", f"{metrics['total_documents']:,}")
    with col2:
        st.metric("Avg Risk Score", f"{metrics['avg_risk_score']:.2f}")
    with col3:
        st.metric("Override Rate", f"{metrics['override_rate']:.1f}%")
    with col4:
        st.metric("Avg Review Time", f"{metrics['avg_review_time']:.1f} min")

    # Row 2: Classification Distribution
    st.subheader("📋 Documents by Classification")
    class_data = data["classification_dist"]
    fig_class = px.bar(
        x=list(class_data.keys()),
        y=list(class_data.values()),
        title="Document Classification Distribution"
    )
    fig_class.update_xaxis(title="Document Type")
    fig_class.update_yaxis(title="Count")
    st.plotly_chart(fig_class, use_container_width=True)

    # Row 3: Risk Score Distribution
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("⚠️ Risk Distribution")
        risk_data = data["risk_dist"]
        fig_risk = px.pie(
            values=list(risk_data.values()),
            names=list(risk_data.keys()),
            title="Risk Level Distribution",
            color_discrete_map={
                "low": "#00c851",
                "medium": "#ff8c00",
                "high": "#ff4b4b"
            }
        )
        st.plotly_chart(fig_risk, use_container_width=True)

    with col2:
        st.subheader("📋 Compliance Gap Frequency")
        gap_data = data["compliance_gaps"]
        fig_gaps = px.bar(
            x=list(gap_data.values()),
            y=list(gap_data.keys()),
            orientation='h',
            title="Most Common Compliance Gaps"
        )
        fig_gaps.update_xaxis(title="Frequency (%)")
        fig_gaps.update_yaxis(title="Regulation")
        st.plotly_chart(fig_gaps, use_container_width=True)

    # Row 4: Agent Performance
    st.subheader("🤖 Agent Performance")

    perf_data = data["agent_performance"]

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**Clause Analysis Agent**")
        st.metric("Avg Latency", f"{perf_data['clause_analysis']['avg_latency']:.1f}s")
        st.metric("Token Usage", f"{perf_data['clause_analysis']['token_usage']:,}")
        st.metric("Error Rate", f"{perf_data['clause_analysis']['error_rate']:.1f}%")

    with col2:
        st.markdown("**Regulatory CrossRef Agent**")
        st.metric("Avg Latency", f"{perf_data['regulatory_crossref']['avg_latency']:.1f}s")
        st.metric("Token Usage", f"{perf_data['regulatory_crossref']['token_usage']:,}")
        st.metric("Error Rate", f"{perf_data['regulatory_crossref']['error_rate']:.1f}%")

    with col3:
        st.markdown("**Briefing Generation Agent**")
        st.metric("Avg Latency", f"{perf_data['briefing_generation']['avg_latency']:.1f}s")
        st.metric("Token Usage", f"{perf_data['briefing_generation']['token_usage']:,}")
        st.metric("Error Rate", f"{perf_data['briefing_generation']['error_rate']:.1f}%")

    # Row 5: Government Compliance Status
    st.subheader("🔒 Government Compliance Status")

    compliance = data["compliance_status"]

    col1, col2 = st.columns(2)

    with col1:
        # FedRAMP Readiness Gauge
        fig_fedramp = go.Figure(go.Indicator(
            mode="gauge+number",
            value=compliance["fedramp_readiness"],
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "FedRAMP Readiness (%)"},
            gauge={
                'axis': {'range': [None, 100]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 60], 'color': "lightcoral"},
                    {'range': [60, 85], 'color': "yellow"},
                    {'range': [85, 100], 'color': "lightgreen"}
                ]
            }
        ))
        fig_fedramp.update_layout(height=300)
        st.plotly_chart(fig_fedramp, use_container_width=True)

    with col2:
        st.markdown("**Compliance Checklist:**")
        st.success(f"✅ KMS Encryption: {'Active' if compliance['kms_encryption'] else 'Inactive'}")
        st.success(f"✅ CloudTrail: {'Enabled' if compliance['cloudtrail_enabled'] else 'Disabled'}")
        st.success(f"✅ Retention Policy: {compliance['retention_policy_years']} years")
        st.info("🔄 Regular compliance audits scheduled")

def main():
    """Main application."""
    load_css()

    # Create sidebar and get demo mode setting
    demo_mode = create_sidebar()

    # Main page title
    st.title("⚖️ Legal Document Classification & Risk Scoring")
    st.markdown("---")

    # Create tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📄 Analyze Document",
        "👨‍💼 Attorney Queue",
        "📁 Batch Processing",
        "📊 Dashboard"
    ])

    with tab1:
        tab_analyze_document(demo_mode)

    with tab2:
        tab_attorney_queue(demo_mode)

    with tab3:
        tab_batch_processing(demo_mode)

    with tab4:
        tab_dashboard(demo_mode)

    # Status indicator
    if demo_mode:
        st.sidebar.success("🎭 Demo Mode Active")
    else:
        st.sidebar.info(f"🌐 API: {API_BASE_URL}")

if __name__ == "__main__":
    main()