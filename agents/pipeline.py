"""
LangGraph pipeline for legal document processing.
Orchestrates the 7-node workflow with conditional routing.
"""
import logging
from typing import Dict, Any, List
from datetime import datetime

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from .state import AgentState, create_initial_state, update_stage_timestamp
from .nodes.extract_text import TextExtractorNode
from .nodes.classify_document import DocumentClassifierNode
from .nodes.clause_analysis import ClauseAnalysisNode
from .nodes.regulatory_crossref import RegulatoryCrossRefNode
from .nodes.risk_scoring import RiskScoringNode
from .nodes.generate_briefing import BriefingGeneratorNode
from .nodes.route_attorney import AttorneyRoutingNode


logger = logging.getLogger(__name__)


class LegalDocumentProcessingPipeline:
    """
    LangGraph-based pipeline for legal document processing.

    Implements a 7-node workflow:
    1. Extract Text (Textract)
    2. Classify Document (SageMaker)
    3. Clause Analysis (Bedrock - parallel)
    4. Regulatory CrossRef (Bedrock - parallel)
    5. Risk Scoring (weighted composite)
    6. Generate Briefing (Bedrock)
    7. Route to Attorney (conditional)
    """

    def __init__(
        self,
        sagemaker_endpoint: str,
        bedrock_region: str = "us-east-1",
        textract_region: str = "us-east-1",
        confidence_threshold: float = 0.5
    ):
        self.confidence_threshold = confidence_threshold

        # Initialize nodes
        self.text_extractor = TextExtractorNode(region_name=textract_region)
        self.document_classifier = DocumentClassifierNode(
            endpoint_name=sagemaker_endpoint,
            region_name=textract_region,
            confidence_threshold=confidence_threshold
        )
        self.clause_analyzer = ClauseAnalysisNode(region_name=bedrock_region)
        self.regulatory_analyzer = RegulatoryCrossRefNode(region_name=bedrock_region)
        self.risk_scorer = RiskScoringNode()
        self.briefing_generator = BriefingGeneratorNode(region_name=bedrock_region)
        self.attorney_router = AttorneyRoutingNode()

        # Build the graph
        self.graph = self._build_graph()

        logger.info("Legal document processing pipeline initialized")

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph state graph."""

        # Create the graph
        workflow = StateGraph(AgentState)

        # Add nodes
        workflow.add_node("extract_text", self._extract_text_node)
        workflow.add_node("classify_document", self._classify_document_node)
        workflow.add_node("clause_analysis", self._clause_analysis_node)
        workflow.add_node("regulatory_crossref", self._regulatory_crossref_node)
        workflow.add_node("risk_scoring", self._risk_scoring_node)
        workflow.add_node("generate_briefing", self._generate_briefing_node)
        workflow.add_node("route_to_attorney", self._route_to_attorney_node)

        # Define the flow
        workflow.set_entry_point("extract_text")

        # Sequential: extract_text -> classify_document
        workflow.add_edge("extract_text", "classify_document")

        # Conditional: classify_document -> (clause_analysis + regulatory_crossref) OR direct routing
        workflow.add_conditional_edges(
            "classify_document",
            self._should_continue_analysis,
            {
                "continue": "clause_analysis",  # Start parallel processing
                "route_direct": "route_to_attorney"  # Low confidence -> direct to senior
            }
        )

        # Parallel processing: clause_analysis and regulatory_crossref
        workflow.add_edge("clause_analysis", "regulatory_crossref")

        # Continue to risk scoring
        workflow.add_edge("regulatory_crossref", "risk_scoring")

        # Sequential: risk_scoring -> generate_briefing -> route_to_attorney
        workflow.add_edge("risk_scoring", "generate_briefing")
        workflow.add_edge("generate_briefing", "route_to_attorney")

        # End at routing
        workflow.add_edge("route_to_attorney", END)

        return workflow

    def _extract_text_node(self, state: AgentState) -> AgentState:
        """Extract text node wrapper."""
        try:
            return self.text_extractor(state)
        except Exception as e:
            logger.error(f"Text extraction node failed: {str(e)}")
            state['errors'].append(f"Text extraction failed: {str(e)}")
            return state

    def _classify_document_node(self, state: AgentState) -> AgentState:
        """Classification node wrapper."""
        try:
            return self.document_classifier(state)
        except Exception as e:
            logger.error(f"Classification node failed: {str(e)}")
            state['errors'].append(f"Classification failed: {str(e)}")
            return state

    def _clause_analysis_node(self, state: AgentState) -> AgentState:
        """Clause analysis node wrapper."""
        try:
            return self.clause_analyzer(state)
        except Exception as e:
            logger.error(f"Clause analysis node failed: {str(e)}")
            state['errors'].append(f"Clause analysis failed: {str(e)}")
            return state

    def _regulatory_crossref_node(self, state: AgentState) -> AgentState:
        """Regulatory crossref node wrapper."""
        try:
            return self.regulatory_analyzer(state)
        except Exception as e:
            logger.error(f"Regulatory crossref node failed: {str(e)}")
            state['errors'].append(f"Regulatory analysis failed: {str(e)}")
            return state

    def _risk_scoring_node(self, state: AgentState) -> AgentState:
        """Risk scoring node wrapper."""
        try:
            return self.risk_scorer(state)
        except Exception as e:
            logger.error(f"Risk scoring node failed: {str(e)}")
            state['errors'].append(f"Risk scoring failed: {str(e)}")
            return state

    def _generate_briefing_node(self, state: AgentState) -> AgentState:
        """Briefing generation node wrapper."""
        try:
            return self.briefing_generator(state)
        except Exception as e:
            logger.error(f"Briefing generation node failed: {str(e)}")
            state['errors'].append(f"Briefing generation failed: {str(e)}")
            return state

    def _route_to_attorney_node(self, state: AgentState) -> AgentState:
        """Attorney routing node wrapper."""
        try:
            return self.attorney_router(state)
        except Exception as e:
            logger.error(f"Attorney routing node failed: {str(e)}")
            state['errors'].append(f"Attorney routing failed: {str(e)}")
            return state

    def _should_continue_analysis(self, state: AgentState) -> str:
        """
        Conditional edge to determine if we should continue with full analysis.

        Args:
            state: Current processing state

        Returns:
            "continue" for full analysis, "route_direct" for direct routing
        """
        confidence = state.get('classification_confidence', 0.0)

        if confidence < self.confidence_threshold:
            logger.info(f"Low confidence ({confidence:.3f}) - routing directly to senior attorney")
            # Set routing decision for direct routing
            state['routing_decision'] = 'senior_attorney_review'
            state['queue_priority'] = 1  # High priority due to uncertainty
            return "route_direct"

        return "continue"

    async def process_document(
        self,
        s3_bucket: str,
        s3_key: str,
        document_id: str = None
    ) -> Dict[str, Any]:
        """
        Process a legal document through the complete pipeline.

        Args:
            s3_bucket: S3 bucket containing the document
            s3_key: S3 key of the document
            document_id: Optional document ID

        Returns:
            Processing results
        """
        logger.info(f"Starting document processing: s3://{s3_bucket}/{s3_key}")

        # Create initial state
        initial_state = create_initial_state(s3_bucket, s3_key, document_id)

        try:
            # Compile and run the graph
            app = self.graph.compile(checkpointer=MemorySaver())

            # Run the pipeline
            config = {"configurable": {"thread_id": initial_state['document_id']}}
            final_state = await app.ainvoke(initial_state, config=config)

            # Extract results
            results = self._extract_results(final_state)

            logger.info(f"Document processing completed: {initial_state['document_id']}")
            logger.info(f"Final routing: {results.get('routing_decision', 'unknown')}")
            logger.info(f"Risk score: {results.get('risk_score', 0):.3f}")

            return results

        except Exception as e:
            logger.error(f"Pipeline execution failed: {str(e)}")
            return {
                'document_id': initial_state['document_id'],
                'status': 'failed',
                'error': str(e),
                'processing_time': (datetime.utcnow() - initial_state['processing_start_time']).total_seconds()
            }

    def process_document_sync(
        self,
        s3_bucket: str,
        s3_key: str,
        document_id: str = None
    ) -> Dict[str, Any]:
        """
        Synchronous version of document processing.

        Args:
            s3_bucket: S3 bucket containing the document
            s3_key: S3 key of the document
            document_id: Optional document ID

        Returns:
            Processing results
        """
        logger.info(f"Starting sync document processing: s3://{s3_bucket}/{s3_key}")

        # Create initial state
        initial_state = create_initial_state(s3_bucket, s3_key, document_id)

        try:
            # Compile and run the graph synchronously
            app = self.graph.compile(checkpointer=MemorySaver())

            # Run the pipeline
            config = {"configurable": {"thread_id": initial_state['document_id']}}
            final_state = app.invoke(initial_state, config=config)

            # Extract results
            results = self._extract_results(final_state)

            logger.info(f"Sync document processing completed: {initial_state['document_id']}")
            logger.info(f"Final routing: {results.get('routing_decision', 'unknown')}")
            logger.info(f"Risk score: {results.get('risk_score', 0):.3f}")

            return results

        except Exception as e:
            logger.error(f"Sync pipeline execution failed: {str(e)}")
            return {
                'document_id': initial_state['document_id'],
                'status': 'failed',
                'error': str(e),
                'processing_time': (datetime.utcnow() - initial_state['processing_start_time']).total_seconds()
            }

    def _extract_results(self, final_state: AgentState) -> Dict[str, Any]:
        """
        Extract structured results from final pipeline state.

        Args:
            final_state: Final state after pipeline execution

        Returns:
            Structured results dictionary
        """
        processing_time = (
            datetime.utcnow() - final_state['processing_start_time']
        ).total_seconds()

        return {
            'document_id': final_state['document_id'],
            'status': 'completed' if not final_state['errors'] else 'completed_with_errors',
            'processing_time': processing_time,

            # Document metadata
            'document_class': final_state.get('document_class'),
            'classification_confidence': final_state.get('classification_confidence'),
            'jurisdiction': final_state.get('jurisdiction'),
            'page_count': final_state.get('page_count'),
            'textract_confidence': final_state.get('textract_confidence'),

            # Analysis results
            'clause_analysis': final_state.get('clause_analysis'),
            'regulatory_analysis': final_state.get('regulatory_analysis'),
            'risk_score': final_state.get('risk_score'),
            'risk_breakdown': final_state.get('risk_breakdown'),

            # Outputs
            'attorney_briefing': final_state.get('attorney_briefing'),
            'routing_decision': final_state.get('routing_decision'),
            'queue_priority': final_state.get('queue_priority'),

            # Processing metadata
            'processing_stages': final_state.get('processing_stages', {}),
            'errors': final_state.get('errors', []),

            # Performance metrics
            'stage_durations': self._calculate_stage_durations(final_state)
        }

    def _calculate_stage_durations(self, state: AgentState) -> Dict[str, float]:
        """Calculate duration for each processing stage."""
        stages = state.get('processing_stages', {})
        start_time = state['processing_start_time']

        durations = {}
        stage_names = [
            'text_extraction_start', 'text_extraction_complete',
            'classification_start', 'classification_complete',
            'clause_analysis_start', 'clause_analysis_complete',
            'regulatory_analysis_start', 'regulatory_analysis_complete',
            'risk_scoring_start', 'risk_scoring_complete',
            'briefing_generation_start', 'briefing_generation_complete',
            'routing_start', 'routing_complete'
        ]

        prev_time = start_time
        for stage in stage_names:
            if stage in stages:
                stage_time = stages[stage]
                if isinstance(stage_time, str):
                    stage_time = datetime.fromisoformat(stage_time.replace('Z', '+00:00'))

                duration = (stage_time - prev_time).total_seconds()
                durations[stage] = duration
                prev_time = stage_time

        return durations

    def get_pipeline_stats(self) -> Dict[str, Any]:
        """Get pipeline configuration and statistics."""
        return {
            'pipeline_version': '1.0.0',
            'nodes': [
                'extract_text', 'classify_document', 'clause_analysis',
                'regulatory_crossref', 'risk_scoring', 'generate_briefing',
                'route_to_attorney'
            ],
            'parallel_nodes': ['clause_analysis', 'regulatory_crossref'],
            'confidence_threshold': self.confidence_threshold,
            'supported_document_classes': [
                'complaint', 'motion', 'contract',
                'regulatory_filing', 'executive_order', 'legislative_text'
            ],
            'routing_options': [
                'auto_file', 'junior_attorney_review', 'senior_attorney_review'
            ]
        }