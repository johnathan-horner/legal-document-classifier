"""
Text extraction node using Amazon Textract.
"""
import boto3
import logging
from typing import Dict, Any, Optional
import json

from ..state import AgentState, update_stage_timestamp, add_error


logger = logging.getLogger(__name__)


class TextExtractorNode:
    """Node for extracting text from documents using Amazon Textract."""

    def __init__(self, region_name: str = "us-east-1"):
        self.textract = boto3.client("textract", region_name=region_name)
        self.s3 = boto3.client("s3", region_name=region_name)

    def __call__(self, state: AgentState) -> AgentState:
        """
        Extract text from document using Amazon Textract.

        Args:
            state: Current processing state

        Returns:
            Updated state with extracted text
        """
        try:
            logger.info(f"Starting text extraction for document {state['document_id']}")
            state = update_stage_timestamp(state, "text_extraction_start")

            # Call Textract
            response = self.textract.analyze_document(
                Document={
                    'S3Object': {
                        'Bucket': state['s3_bucket'],
                        'Name': state['s3_key']
                    }
                },
                FeatureTypes=['TABLES', 'FORMS']  # Extract tables and forms as well
            )

            # Extract text and confidence
            extracted_text, avg_confidence, page_count = self._process_textract_response(response)

            # Update state
            state['extracted_text'] = extracted_text
            state['textract_confidence'] = avg_confidence
            state['page_count'] = page_count

            state = update_stage_timestamp(state, "text_extraction_complete")
            logger.info(f"Text extraction completed. Length: {len(extracted_text)} chars, "
                       f"Confidence: {avg_confidence:.3f}")

            return state

        except Exception as e:
            error_msg = f"Text extraction failed: {str(e)}"
            logger.error(error_msg)
            state = add_error(state, error_msg)
            # Set minimal values to allow pipeline to continue
            state['extracted_text'] = ""
            state['textract_confidence'] = 0.0
            state['page_count'] = 0
            return state

    def _process_textract_response(
        self,
        response: Dict[str, Any]
    ) -> tuple[str, float, int]:
        """
        Process Textract response to extract text and calculate confidence.

        Args:
            response: Textract API response

        Returns:
            Tuple of (extracted_text, average_confidence, page_count)
        """
        blocks = response.get('Blocks', [])

        # Extract text blocks
        text_blocks = []
        confidence_scores = []
        pages = set()

        for block in blocks:
            if block['BlockType'] == 'LINE':
                text = block.get('Text', '').strip()
                if text:
                    text_blocks.append(text)
                    confidence_scores.append(block.get('Confidence', 0))
                    pages.add(block.get('Page', 1))

            elif block['BlockType'] == 'TABLE':
                # Extract table text
                table_text = self._extract_table_text(block, blocks)
                if table_text:
                    text_blocks.append(table_text)
                    confidence_scores.append(block.get('Confidence', 0))
                    pages.add(block.get('Page', 1))

        # Combine text
        extracted_text = '\n'.join(text_blocks)

        # Calculate average confidence
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0

        # Get page count
        page_count = len(pages) if pages else 1

        return extracted_text, avg_confidence, page_count

    def _extract_table_text(self, table_block: Dict[str, Any], all_blocks: List[Dict[str, Any]]) -> str:
        """Extract text from table blocks."""
        # This is a simplified table extraction
        # In production, you might want more sophisticated table processing
        table_text = []

        if 'Relationships' in table_block:
            for relationship in table_block['Relationships']:
                if relationship['Type'] == 'CHILD':
                    for child_id in relationship['Ids']:
                        child_block = next(
                            (block for block in all_blocks if block['Id'] == child_id),
                            None
                        )
                        if child_block and child_block['BlockType'] == 'CELL':
                            cell_text = self._extract_cell_text(child_block, all_blocks)
                            if cell_text:
                                table_text.append(cell_text)

        return ' | '.join(table_text) if table_text else ""

    def _extract_cell_text(self, cell_block: Dict[str, Any], all_blocks: List[Dict[str, Any]]) -> str:
        """Extract text from table cell."""
        cell_text = []

        if 'Relationships' in cell_block:
            for relationship in cell_block['Relationships']:
                if relationship['Type'] == 'CHILD':
                    for child_id in relationship['Ids']:
                        child_block = next(
                            (block for block in all_blocks if block['Id'] == child_id),
                            None
                        )
                        if child_block and child_block['BlockType'] == 'WORD':
                            text = child_block.get('Text', '').strip()
                            if text:
                                cell_text.append(text)

        return ' '.join(cell_text)

    def validate_extraction(self, state: AgentState) -> bool:
        """
        Validate that text extraction was successful.

        Args:
            state: Processing state

        Returns:
            True if extraction is valid
        """
        if not state.get('extracted_text'):
            return False

        if state.get('textract_confidence', 0) < 0.3:  # Low confidence threshold
            logger.warning(f"Low Textract confidence: {state.get('textract_confidence')}")

        # Check minimum text length
        text_length = len(state['extracted_text'].strip())
        if text_length < 50:  # Minimum viable document length
            logger.warning(f"Extracted text too short: {text_length} characters")
            return False

        return True