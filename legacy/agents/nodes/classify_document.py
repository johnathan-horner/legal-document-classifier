"""
Document classification node using SageMaker endpoint.
"""
import boto3
import json
import logging
import re
from typing import Dict, Any, Optional, List

from ..state import AgentState, update_stage_timestamp, add_error


logger = logging.getLogger(__name__)


class DocumentClassifierNode:
    """Node for classifying documents using SageMaker endpoint."""

    def __init__(
        self,
        endpoint_name: str,
        region_name: str = "us-east-1",
        confidence_threshold: float = 0.5
    ):
        self.endpoint_name = endpoint_name
        self.confidence_threshold = confidence_threshold
        self.sagemaker_runtime = boto3.client("sagemaker-runtime", region_name=region_name)

        # Document class mappings
        self.class_names = [
            "complaint", "motion", "contract",
            "regulatory_filing", "executive_order", "legislative_text"
        ]

        # Jurisdiction patterns for extraction
        self.jurisdiction_patterns = [
            r"State of (\w+)",
            r"(\w+) State",
            r"jurisdiction.*?(\w+)",
            r"laws of (\w+)",
            r"Superior Court of (\w+)",
            r"(\w+) Superior Court"
        ]

    def __call__(self, state: AgentState) -> AgentState:
        """
        Classify document using SageMaker endpoint.

        Args:
            state: Current processing state

        Returns:
            Updated state with classification results
        """
        try:
            logger.info(f"Starting document classification for {state['document_id']}")
            state = update_stage_timestamp(state, "classification_start")

            # Extract jurisdiction first
            jurisdiction = self._extract_jurisdiction(state['extracted_text'])
            state['jurisdiction'] = jurisdiction

            # Prepare text for classification
            processed_text = self._preprocess_text(state['extracted_text'])

            # Call SageMaker endpoint
            response = self.sagemaker_runtime.invoke_endpoint(
                EndpointName=self.endpoint_name,
                ContentType='application/json',
                Body=json.dumps({
                    'inputs': processed_text
                })
            )

            # Parse response
            result = json.loads(response['Body'].read().decode())
            document_class, confidence = self._parse_classification_result(result)

            # Update state
            state['document_class'] = document_class
            state['classification_confidence'] = confidence

            state = update_stage_timestamp(state, "classification_complete")
            logger.info(f"Classification completed: {document_class} (confidence: {confidence:.3f})")

            return state

        except Exception as e:
            error_msg = f"Document classification failed: {str(e)}"
            logger.error(error_msg)
            state = add_error(state, error_msg)
            # Set default values
            state['document_class'] = "unknown"
            state['classification_confidence'] = 0.0
            state['jurisdiction'] = "unknown"
            return state

    def _preprocess_text(self, text: str) -> str:
        """
        Preprocess text for classification.

        Args:
            text: Raw extracted text

        Returns:
            Preprocessed text
        """
        if not text:
            return ""

        # Clean up text
        text = re.sub(r'\s+', ' ', text)  # Normalize whitespace
        text = text.strip()

        # Truncate if too long (model has max length limit)
        max_length = 4000  # Conservative limit for tokenization
        if len(text) > max_length:
            text = text[:max_length] + "..."

        return text

    def _extract_jurisdiction(self, text: str) -> str:
        """
        Extract jurisdiction from document text.

        Args:
            text: Document text

        Returns:
            Extracted jurisdiction or "unknown"
        """
        if not text:
            return "unknown"

        text_lower = text.lower()

        # Common U.S. states and jurisdictions
        jurisdictions = [
            "delaware", "new york", "california", "texas", "florida",
            "illinois", "nevada", "massachusetts", "virginia", "washington",
            "maryland", "pennsylvania", "georgia", "north carolina",
            "new jersey", "michigan", "ohio", "indiana", "tennessee",
            "missouri", "wisconsin", "minnesota", "colorado", "alabama",
            "south carolina", "louisiana", "kentucky", "oregon", "oklahoma",
            "connecticut", "utah", "iowa", "arkansas", "mississippi",
            "kansas", "new mexico", "nebraska", "west virginia", "idaho",
            "hawaii", "new hampshire", "maine", "montana", "rhode island",
            "delaware", "south dakota", "north dakota", "alaska", "vermont", "wyoming"
        ]

        # Look for explicit jurisdiction mentions
        for pattern in self.jurisdiction_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                match_lower = match.lower()
                if match_lower in jurisdictions:
                    return match.title()

        # Look for state names in the text
        for jurisdiction in jurisdictions:
            if jurisdiction in text_lower:
                return jurisdiction.title()

        # Federal indicators
        if any(term in text_lower for term in ["federal", "united states", "u.s.", "congress", "senate", "house of representatives"]):
            return "Federal"

        return "unknown"

    def _parse_classification_result(self, result: Dict[str, Any]) -> tuple[str, float]:
        """
        Parse SageMaker endpoint response.

        Args:
            result: SageMaker response

        Returns:
            Tuple of (document_class, confidence)
        """
        # Handle different possible response formats
        if 'predictions' in result:
            predictions = result['predictions']
            if isinstance(predictions, list) and len(predictions) > 0:
                prediction = predictions[0]
            else:
                prediction = predictions

            if isinstance(prediction, dict):
                if 'label' in prediction and 'score' in prediction:
                    return prediction['label'], prediction['score']
                elif 'predicted_label' in prediction and 'confidence' in prediction:
                    return prediction['predicted_label'], prediction['confidence']

        elif 'predicted_label' in result and 'probabilities' in result:
            predicted_idx = result['predicted_label']
            probabilities = result['probabilities']
            if isinstance(predicted_idx, int) and predicted_idx < len(self.class_names):
                return self.class_names[predicted_idx], max(probabilities)

        elif isinstance(result, dict) and 'class' in result and 'confidence' in result:
            return result['class'], result['confidence']

        # Fallback parsing - try to extract any numeric confidence
        confidence = 0.0
        doc_class = "unknown"

        # Look for confidence scores in the response
        def extract_numbers(obj):
            if isinstance(obj, (int, float)):
                return [float(obj)]
            elif isinstance(obj, str):
                numbers = re.findall(r'\d+\.?\d*', obj)
                return [float(n) for n in numbers]
            elif isinstance(obj, list):
                nums = []
                for item in obj:
                    nums.extend(extract_numbers(item))
                return nums
            elif isinstance(obj, dict):
                nums = []
                for value in obj.values():
                    nums.extend(extract_numbers(value))
                return nums
            return []

        numbers = extract_numbers(result)
        if numbers:
            confidence = max([n for n in numbers if 0 <= n <= 1] + [0])

        logger.warning(f"Could not parse SageMaker response format: {result}")
        return doc_class, confidence

    def should_route_to_senior(self, state: AgentState) -> bool:
        """
        Determine if document should be routed directly to senior attorney due to low confidence.

        Args:
            state: Current processing state

        Returns:
            True if should route to senior attorney
        """
        confidence = state.get('classification_confidence', 0.0)
        return confidence < self.confidence_threshold

    def get_classification_summary(self, state: AgentState) -> Dict[str, Any]:
        """
        Get summary of classification results.

        Args:
            state: Current processing state

        Returns:
            Classification summary
        """
        return {
            'document_class': state.get('document_class', 'unknown'),
            'confidence': state.get('classification_confidence', 0.0),
            'jurisdiction': state.get('jurisdiction', 'unknown'),
            'low_confidence': self.should_route_to_senior(state),
            'textract_confidence': state.get('textract_confidence', 0.0),
            'page_count': state.get('page_count', 0),
            'text_length': len(state.get('extracted_text', ''))
        }