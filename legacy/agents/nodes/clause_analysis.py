"""
Clause analysis node using LangChain + Amazon Bedrock.
"""
import logging
from typing import Dict, Any, List, Optional
import json
import re
from datetime import datetime

from langchain_aws import ChatBedrock
from langchain.schema import HumanMessage, SystemMessage
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

from ..state import AgentState, update_stage_timestamp, add_error, ClauseAnalysis


logger = logging.getLogger(__name__)


class ClauseDetectionResult(BaseModel):
    """Pydantic model for structured clause detection output."""

    clauses_found: List[ClauseAnalysis] = Field(
        description="List of detected high-risk clauses with analysis"
    )
    overall_risk_assessment: str = Field(
        description="Overall risk assessment of the document clauses"
    )
    unusual_language: List[str] = Field(
        description="List of unusual or non-standard language identified"
    )
    recommendations: List[str] = Field(
        description="Recommendations for clause review or modification"
    )


class ClauseAnalysisNode:
    """Node for analyzing legal clauses using Amazon Bedrock."""

    def __init__(
        self,
        model_id: str = "anthropic.claude-3-sonnet-20240229-v1:0",
        region_name: str = "us-east-1"
    ):
        self.llm = ChatBedrock(
            model_id=model_id,
            region_name=region_name,
            model_kwargs={
                "temperature": 0.1,
                "top_p": 0.9,
                "max_tokens": 4000
            }
        )

        # Output parser for structured responses
        self.parser = PydanticOutputParser(pydantic_object=ClauseDetectionResult)

        # Clause types to detect
        self.target_clause_types = [
            "indemnification",
            "liability_limitation",
            "termination",
            "non_compete",
            "data_sharing",
            "penalty_provisions"
        ]

    def __call__(self, state: AgentState) -> AgentState:
        """
        Analyze document clauses using Bedrock.

        Args:
            state: Current processing state

        Returns:
            Updated state with clause analysis
        """
        try:
            logger.info(f"Starting clause analysis for document {state['document_id']}")
            state = update_stage_timestamp(state, "clause_analysis_start")

            # Get document text and metadata
            document_text = state['extracted_text']
            document_class = state.get('document_class', 'unknown')

            if not document_text or len(document_text.strip()) < 100:
                logger.warning("Document text too short for clause analysis")
                state['clause_analysis'] = self._empty_analysis()
                state['detected_clauses'] = []
                return state

            # Perform clause analysis
            analysis_result = self._analyze_clauses(document_text, document_class)

            # Update state
            state['clause_analysis'] = {
                'clauses_found': [clause.__dict__ for clause in analysis_result.clauses_found],
                'overall_risk_assessment': analysis_result.overall_risk_assessment,
                'unusual_language': analysis_result.unusual_language,
                'recommendations': analysis_result.recommendations,
                'analysis_timestamp': datetime.utcnow().isoformat()
            }

            state['detected_clauses'] = [clause.__dict__ for clause in analysis_result.clauses_found]

            state = update_stage_timestamp(state, "clause_analysis_complete")
            logger.info(f"Clause analysis completed. Found {len(analysis_result.clauses_found)} high-risk clauses")

            return state

        except Exception as e:
            error_msg = f"Clause analysis failed: {str(e)}"
            logger.error(error_msg)
            state = add_error(state, error_msg)
            state['clause_analysis'] = self._empty_analysis()
            state['detected_clauses'] = []
            return state

    def _analyze_clauses(self, document_text: str, document_class: str) -> ClauseDetectionResult:
        """
        Analyze clauses in the document text.

        Args:
            document_text: Full document text
            document_class: Classified document type

        Returns:
            Structured clause analysis result
        """
        # Chunk document if too long
        text_chunks = self._chunk_text(document_text, max_chunk_size=3000)

        all_clauses = []
        all_unusual_language = []
        all_recommendations = []

        for i, chunk in enumerate(text_chunks):
            logger.info(f"Analyzing chunk {i+1}/{len(text_chunks)}")

            # Create prompt for this chunk
            prompt = self._create_clause_analysis_prompt(chunk, document_class)

            try:
                # Get LLM response
                messages = [
                    SystemMessage(content=self._get_system_prompt()),
                    HumanMessage(content=prompt)
                ]

                response = self.llm.invoke(messages)
                result_text = response.content

                # Parse structured output
                chunk_result = self._parse_llm_response(result_text)

                all_clauses.extend(chunk_result.clauses_found)
                all_unusual_language.extend(chunk_result.unusual_language)
                all_recommendations.extend(chunk_result.recommendations)

            except Exception as e:
                logger.error(f"Error analyzing chunk {i+1}: {str(e)}")
                continue

        # Consolidate results
        consolidated_clauses = self._consolidate_clauses(all_clauses)
        unique_language = list(set(all_unusual_language))
        unique_recommendations = list(set(all_recommendations))

        # Generate overall risk assessment
        overall_risk = self._assess_overall_risk(consolidated_clauses)

        return ClauseDetectionResult(
            clauses_found=consolidated_clauses,
            overall_risk_assessment=overall_risk,
            unusual_language=unique_language,
            recommendations=unique_recommendations
        )

    def _get_system_prompt(self) -> str:
        """Get the system prompt for clause analysis."""
        return """You are a senior legal analyst specializing in contract and legal document review.
Your task is to identify and analyze high-risk clauses in legal documents.

Focus on detecting these specific clause types:
1. Indemnification clauses - provisions requiring one party to compensate another for losses
2. Liability limitation clauses - provisions limiting damages or liability
3. Termination clauses - provisions governing how agreements can be ended
4. Non-compete clauses - restrictions on competitive activities
5. Data sharing clauses - provisions governing data access and usage
6. Penalty provisions - monetary penalties or liquidated damages

For each clause found:
- Identify the specific clause type
- Extract the relevant text excerpt
- Assess risk level (low, medium, high)
- Provide confidence score (0.0-1.0)
- Explain the legal implications
- Note any regulatory implications

Also identify any unusual or non-standard language that might require special attention.

Provide clear, actionable analysis that would help an attorney quickly understand the document's risk profile."""

    def _create_clause_analysis_prompt(self, text_chunk: str, document_class: str) -> str:
        """Create analysis prompt for a text chunk."""
        format_instructions = self.parser.get_format_instructions()

        prompt = f"""
Analyze the following {document_class} document excerpt for high-risk legal clauses:

DOCUMENT TEXT:
{text_chunk}

ANALYSIS REQUIREMENTS:
1. Identify any of these high-risk clause types:
   - Indemnification clauses
   - Liability limitation clauses
   - Termination clauses
   - Non-compete clauses
   - Data sharing clauses
   - Penalty provisions

2. For each clause found, provide:
   - Clause type
   - Specific text excerpt (quoted directly from document)
   - Risk level assessment (low/medium/high)
   - Confidence score (0.0-1.0)
   - Clear explanation of risks and implications

3. Identify any unusual or non-standard legal language

4. Provide recommendations for review or action

{format_instructions}

Be thorough but focus only on genuinely high-risk provisions. Provide specific text excerpts and clear risk assessments.
"""
        return prompt

    def _chunk_text(self, text: str, max_chunk_size: int = 3000) -> List[str]:
        """
        Chunk document text for processing.

        Args:
            text: Full document text
            max_chunk_size: Maximum characters per chunk

        Returns:
            List of text chunks
        """
        if len(text) <= max_chunk_size:
            return [text]

        chunks = []
        current_pos = 0

        while current_pos < len(text):
            end_pos = current_pos + max_chunk_size

            if end_pos >= len(text):
                chunks.append(text[current_pos:])
                break

            # Try to break at a sentence boundary
            chunk_text = text[current_pos:end_pos]
            last_period = chunk_text.rfind('.')
            last_newline = chunk_text.rfind('\n')

            break_pos = max(last_period, last_newline)
            if break_pos > 0:
                end_pos = current_pos + break_pos + 1

            chunks.append(text[current_pos:end_pos])
            current_pos = end_pos

        return [chunk.strip() for chunk in chunks if chunk.strip()]

    def _parse_llm_response(self, response_text: str) -> ClauseDetectionResult:
        """
        Parse LLM response into structured format.

        Args:
            response_text: Raw LLM response

        Returns:
            Parsed clause detection result
        """
        try:
            # Try structured parsing first
            return self.parser.parse(response_text)
        except Exception as e:
            logger.warning(f"Structured parsing failed, using fallback: {str(e)}")
            return self._fallback_parse(response_text)

    def _fallback_parse(self, response_text: str) -> ClauseDetectionResult:
        """
        Fallback parsing when structured parsing fails.

        Args:
            response_text: Raw LLM response

        Returns:
            Best-effort parsed result
        """
        clauses = []
        unusual_language = []
        recommendations = []

        # Extract clauses using pattern matching
        clause_patterns = [
            r"indemnif(?:y|ication)",
            r"liability.*?limit",
            r"terminat(?:e|ion)",
            r"non[- ]?compet",
            r"data.*?shar",
            r"penalt(?:y|ies)"
        ]

        for clause_type, pattern in zip(self.target_clause_types, clause_patterns):
            matches = re.finditer(pattern, response_text.lower())
            for match in matches:
                # Extract surrounding context
                start = max(0, match.start() - 100)
                end = min(len(response_text), match.end() + 100)
                excerpt = response_text[start:end].strip()

                if len(excerpt) > 20:  # Minimum viable excerpt
                    clause = ClauseAnalysis(
                        clause_type=clause_type,
                        text_excerpt=excerpt,
                        risk_level="medium",  # Default
                        confidence=0.6,  # Default
                        explanation=f"Detected {clause_type} clause",
                        regulatory_implications=[]
                    )
                    clauses.append(clause)

        # Extract recommendations
        rec_patterns = [
            r"recommend(?:ation)?s?:?\s*([^.\n]+)",
            r"suggest(?:ion)?s?:?\s*([^.\n]+)"
        ]

        for pattern in rec_patterns:
            matches = re.finditer(pattern, response_text, re.IGNORECASE)
            for match in matches:
                rec = match.group(1).strip()
                if len(rec) > 10:
                    recommendations.append(rec)

        return ClauseDetectionResult(
            clauses_found=clauses,
            overall_risk_assessment="Moderate risk identified - requires review",
            unusual_language=unusual_language,
            recommendations=recommendations
        )

    def _consolidate_clauses(self, clauses: List[ClauseAnalysis]) -> List[ClauseAnalysis]:
        """
        Consolidate duplicate or similar clauses.

        Args:
            clauses: List of detected clauses

        Returns:
            Consolidated list of unique clauses
        """
        if not clauses:
            return []

        # Group by clause type
        clause_groups = {}
        for clause in clauses:
            if clause.clause_type not in clause_groups:
                clause_groups[clause.clause_type] = []
            clause_groups[clause.clause_type].append(clause)

        consolidated = []
        for clause_type, group in clause_groups.items():
            if len(group) == 1:
                consolidated.append(group[0])
            else:
                # Take the highest confidence clause of each type
                best_clause = max(group, key=lambda c: c.confidence)
                consolidated.append(best_clause)

        return consolidated

    def _assess_overall_risk(self, clauses: List[ClauseAnalysis]) -> str:
        """
        Assess overall document risk based on detected clauses.

        Args:
            clauses: List of detected clauses

        Returns:
            Overall risk assessment string
        """
        if not clauses:
            return "Low risk - no high-risk clauses detected"

        high_risk_count = sum(1 for c in clauses if c.risk_level == "high")
        medium_risk_count = sum(1 for c in clauses if c.risk_level == "medium")

        if high_risk_count > 0:
            return f"High risk - {high_risk_count} high-risk clauses identified requiring immediate attorney review"
        elif medium_risk_count > 2:
            return f"Medium-high risk - {medium_risk_count} moderate-risk clauses requiring review"
        elif medium_risk_count > 0:
            return f"Moderate risk - {medium_risk_count} moderate-risk clauses identified"
        else:
            return "Low-moderate risk - some clauses require standard review"

    def _empty_analysis(self) -> Dict[str, Any]:
        """Return empty analysis structure."""
        return {
            'clauses_found': [],
            'overall_risk_assessment': 'Unable to perform clause analysis',
            'unusual_language': [],
            'recommendations': ['Manual review required due to analysis failure'],
            'analysis_timestamp': datetime.utcnow().isoformat()
        }