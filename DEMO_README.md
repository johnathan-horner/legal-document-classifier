# Legal Document Classification & Risk Scoring - Streamlit Demo

A comprehensive demo frontend for the Legal Document Classification & Risk Scoring System built with Streamlit.

## 🎯 Demo Mode (Portfolio Ready)

The app includes a **Demo Mode** that provides realistic mock data, allowing you to demonstrate the full system without running the AWS backend infrastructure. Perfect for:

- Portfolio demonstrations
- Interview presentations
- Client demos
- System walkthroughs

## 🚀 Quick Start

### Option 1: One-Click Launch (Recommended)
```bash
./run_demo.sh
```

### Option 2: Manual Setup
```bash
# Install dependencies
pip install -r streamlit_requirements.txt

# Launch app
streamlit run app.py
```

The demo will open at `http://localhost:8501`

## 📱 Features

### 📄 **Tab 1: Analyze Document**
- Upload PDF/TXT files or use Demo Mode with sample contract
- Real-time processing pipeline visualization:
  - Amazon Textract text extraction
  - DistilBERT document classification
  - Parallel LangGraph agents (clause analysis + regulatory crossref)
  - Risk scoring and attorney briefing generation
- Interactive results with risk gauge and routing decisions
- PDF briefing export functionality

### 👨‍💼 **Tab 2: Attorney Queue**
- Role-based access simulation (Junior/Senior Attorney, Department Head)
- Document queue management with risk-based prioritization
- Detailed document inspection with flagged clauses
- Feedback system (confirm, override, mark reviewed)

### 📁 **Tab 3: Batch Processing**
- Multi-file upload and processing
- Progress tracking and batch results
- Summary statistics and risk distribution charts

### 📊 **Tab 4: Dashboard**
- Executive metrics dashboard
- Document classification and risk distribution charts
- Compliance gap analysis
- Multi-agent performance monitoring
- Government compliance status (FedRAMP readiness)

## 🎭 Demo Mode Mock Data

Realistic mock responses include:

**Document Analysis:**
- Government contract classified as "contract" (91% confidence)
- 4 flagged clauses with detailed risk assessments
- 3 compliance gaps (FAR regulations, FISMA, Privacy Act)
- Risk score: 0.74 → Senior Attorney review

**Attorney Queue:**
- 8 diverse documents across all classification types
- Varied risk scores and jurisdictions
- Different workflow statuses

**Dashboard Metrics:**
- 3,412 documents processed
- 0.41 average risk score
- 8% override rate
- Detailed compliance and performance analytics

## 📁 Sample Documents

Three realistic legal documents included in `/samples`:
- `government_contract.txt` - Federal cybersecurity services contract
- `regulatory_filing.txt` - SEC Form 10-Q quarterly report
- `civil_complaint.txt` - Federal court employment law complaint

## 🛠️ Architecture

The Streamlit app is a **frontend-only** demo that:
- Calls REST API endpoints (real or mocked)
- Does NOT contain model logic or LangGraph agents
- Provides complete UI/UX demonstration
- Shows realistic data flows and processing results

## 🔧 Configuration

### Environment Variables
```bash
API_BASE_URL=http://localhost:8000  # Backend API URL (optional in demo mode)
```

### API Integration
When Demo Mode is disabled, the app expects these API endpoints:
- `POST /analyze` - Document analysis
- `GET /queue/{role}` - Attorney queue by role
- `POST /batch` - Batch processing
- `GET /dashboard/*` - Dashboard metrics
- `POST /feedback/{doc_id}` - Attorney feedback

## 🎨 UI Features

- **Professional Design**: Clean, government-ready interface
- **Dark Theme Friendly**: Consistent styling across themes
- **Responsive Layout**: Wide layout with optimized columns
- **Interactive Charts**: Plotly visualizations for metrics
- **Real-time Updates**: Processing pipeline with status indicators
- **Export Functionality**: PDF briefing generation

## 🚀 Deployment

### Local Development
```bash
streamlit run app.py --server.port 8501
```

### Production Deployment
The Streamlit app can be deployed to:
- Streamlit Cloud (streamlit.io)
- AWS ECS/Fargate
- Docker containers
- Any Python hosting platform

### Docker Deployment
```bash
# Build image
docker build -t legal-doc-demo .

# Run container
docker run -p 8501:8501 legal-doc-demo
```

## 📋 Requirements

- Python 3.11+
- Streamlit 1.28+
- See `streamlit_requirements.txt` for full dependencies

## 🎯 Portfolio Usage

Perfect for demonstrating:
- **Full-stack AI system architecture**
- **Government/legal domain expertise**
- **Multi-agent LangGraph workflows**
- **AWS cloud-native design**
- **Professional UI/UX development**
- **Production-ready demo capabilities**

The Demo Mode ensures you can showcase the complete system functionality anytime, anywhere, without infrastructure dependencies.

## 📧 Support

Built by **Johnathan Horner** - [GitHub Repository](https://github.com/johnathan-horner/legal-document-classifier)