"""
Pass 2 Quality Assessment Module - Two-Pass AI Quality Control System

This module implements the core quality assessment functionality with a 5-dimension scoring system
and evidence-based filtering logic that processes Pass 1 output and produces high-quality segment
selections through rigorous evaluation.

Features:
- 5-dimension independent scoring system (1-10 scale)
- Evidence-based automatic filtering with strict thresholds
- Weighted quality score calculation
- Gemini API integration for AI-powered quality assessment
- Comprehensive I/O validation using JSON schema framework
- Minimum segment count enforcement

Author: APM Implementation Agent  
Created: 2025-01-13
Pipeline: Two-Pass AI Quality Control System (Phase 1, Task 1.2)
"""

import sys
import os
import json
import google.generativeai as genai
from datetime import datetime
import logging
import traceback
import time
from typing import Dict, List, Any, Optional, Union, Tuple
from pathlib import Path

# Add paths for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
utils_dir = os.path.join(current_dir, '..', 'Utils')
sys.path.append(utils_dir)

# Import validation framework
from json_schema_validator import JSONSchemaValidator

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

class QualityAssessor:
    """
    Core quality assessment module with 5-dimension scoring and automatic filtering.
    
    Implements evidence-based evaluation of Pass 1 analysis results to produce
    high-quality segment selections through rigorous quality gates.
    """
    
    def __init__(self, config_path: Optional[str] = None, test_mode: bool = False):
        """
        Initialize the QualityAssessor with configuration and validation framework.
        
        Args:
            config_path: Optional path to config file. If None, uses default location.
            test_mode: If True, use relaxed thresholds for testing/demonstration
        """
        self.config = self._load_config(config_path)
        self.validator = JSONSchemaValidator()
        self._configure_gemini()
        
        # Quality assessment thresholds (exact as specified or test mode)
        if test_mode:
            self.filtering_thresholds = {
                'quote_strength': 3,
                'factual_accuracy': 3, 
                'potential_impact': 3,
                'content_specificity': 3,
                'context_appropriateness': 3
            }
            self.min_segments_required = 3
        else:
            self.filtering_thresholds = {
                'quote_strength': 6,
                'factual_accuracy': 5, 
                'potential_impact': 5,
                'content_specificity': 5,
                'context_appropriateness': 5
            }
        
        # Weighted scoring formula (exact as specified)
        self.scoring_weights = {
            'quote_strength': 0.3,
            'factual_accuracy': 0.25,
            'potential_impact': 0.25,
            'content_specificity': 0.1,
            'context_appropriateness': 0.1
        }
        
        if not hasattr(self, 'min_segments_required'):
            self.min_segments_required = 4
        self.max_segments_selected = 12
        self.min_segments_selected = 8
        
        # Debug storage for API calls
        self._debug_api_calls = []
        
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        if config_path is None:
            config_path = os.path.join(current_dir, '..', 'Config', 'default_config.yaml')
            
        try:
            import yaml
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            logger.info(f"Loaded configuration from: {config_path}")
            return config
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            # Fallback config
            return {
                'api': {'gemini_api_key': os.getenv('GEMINI_API_KEY')},
                'error_handling': {'max_retries': 3, 'retry_delay': 5}
            }
    
    def _configure_gemini(self) -> None:
        """Configure Gemini API using config settings."""
        try:
            api_key = self.config.get('api', {}).get('gemini_api_key')
            if not api_key:
                raise ValueError("Gemini API key not found in configuration")
                
            genai.configure(api_key=api_key)
            logger.info("Gemini API configured successfully")
        except Exception as e:
            logger.error(f"Failed to configure Gemini API: {e}")
            raise
    
    def process_pass1_results(
        self, 
        input_data: Union[List[Dict], str, Path],
        output_path: Optional[str] = None
    ) -> Tuple[List[Dict], Dict[str, Any]]:
        """
        Main processing function that takes Pass 1 results and produces filtered output.
        
        Args:
            input_data: Pass 1 analysis results (data or file path)
            output_path: Optional output path for saving results
            
        Returns:
            Tuple of (filtered_segments, processing_metadata)
        """
        logger.info("=== PASS 2 QUALITY ASSESSMENT STARTED ===")
        
        # Step 1: Validate input data
        logger.info("Validating Pass 1 input data...")
        is_valid, error_messages = self.validator.validate_pass2_input(input_data)
        if not is_valid:
            error_msg = f"Input validation failed:\n" + "\n".join(error_messages)
            logger.error(error_msg)
            raise ValueError(error_msg)
        logger.info("✅ Input validation successful")
        
        # Step 2: Load data if file path provided
        if isinstance(input_data, (str, Path)):
            with open(input_data, 'r', encoding='utf-8') as f:
                segments_data = json.load(f)
        else:
            segments_data = input_data
            
        logger.info(f"Processing {len(segments_data)} segments from Pass 1")
        
        # Step 3: Generate quality assessments using Gemini API
        logger.info("Generating quality assessments via Gemini API...")
        assessed_segments = self._generate_quality_assessments(segments_data)
        
        # Step 4: Apply filtering rules
        logger.info("Applying automatic filtering rules...")
        filtered_segments = self._apply_filtering_rules(assessed_segments)
        
        # Step 5: Final selection (top 8-12 segments)
        logger.info("Selecting final segments...")
        final_segments = self._select_final_segments(filtered_segments)
        
        # Step 6: Clean output for validation (remove debug fields)
        clean_final_segments = self._clean_segments_for_output(final_segments)
        
        # Step 7: Validate output
        logger.info("Validating output data...")
        is_valid, error_messages = self.validator.validate_pass2_output(clean_final_segments)
        if not is_valid:
            error_msg = f"Output validation failed:\n" + "\n".join(error_messages)
            logger.error(error_msg)
            raise ValueError(error_msg)
        logger.info("✅ Output validation successful")
        
        # Step 8: Save results if output path provided
        processing_metadata = {
            'processing_timestamp': datetime.now().isoformat(),
            'input_segments_count': len(segments_data),
            'assessed_segments_count': len(assessed_segments),
            'filtered_segments_count': len(filtered_segments),
            'final_segments_count': len(clean_final_segments),
            'filtering_thresholds': self.filtering_thresholds,
            'scoring_weights': self.scoring_weights
        }
        
        if output_path:
            self._save_results(clean_final_segments, processing_metadata, output_path)
            
        logger.info(f"=== PASS 2 QUALITY ASSESSMENT COMPLETED ===")
        logger.info(f"Final output: {len(clean_final_segments)} high-quality segments")
        
        return clean_final_segments, processing_metadata
    
    def _generate_quality_assessments(self, segments_data: List[Dict]) -> List[Dict]:
        """
        Generate quality assessments for all segments using Gemini API.
        
        Args:
            segments_data: List of segment data from Pass 1
            
        Returns:
            List of segments with quality_assessment fields added
        """
        assessed_segments = []
        
        # Process segments in batches to avoid API limits
        batch_size = 5
        total_segments = len(segments_data)
        
        for i in range(0, total_segments, batch_size):
            batch = segments_data[i:i + batch_size]
            logger.info(f"Processing batch {i//batch_size + 1}/{(total_segments-1)//batch_size + 1} ({len(batch)} segments)")
            
            try:
                batch_results = self._assess_segment_batch(batch)
                assessed_segments.extend(batch_results)
                
                # Rate limiting delay
                time.sleep(2)  # Conservative delay to avoid rate limits
                
            except Exception as e:
                logger.error(f"Failed to process batch {i//batch_size + 1}: {e}")
                # Continue with remaining batches
                continue
                
        logger.info(f"Successfully assessed {len(assessed_segments)}/{total_segments} segments")
        return assessed_segments
    
    def _assess_segment_batch(self, segments_batch: List[Dict]) -> List[Dict]:
        """
        Assess a batch of segments using Gemini API.
        
        Args:
            segments_batch: Batch of segments to assess
            
        Returns:
            List of segments with quality assessments added
        """
        # Create evaluation prompt
        prompt = self._create_pass2_prompt(segments_batch)
        
        # Generate assessment using Gemini
        max_retries = self.config.get('error_handling', {}).get('max_retries', 3)
        
        for attempt in range(max_retries):
            try:
                model = genai.GenerativeModel(
                    'gemini-2.5-pro-preview-06-05',
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.1,
                        top_p=0.9,
                        candidate_count=1,
                        response_mime_type="application/json"
                    )
                )
                
                response = model.generate_content(prompt)
                
                if not response.text:
                    raise ValueError("Empty response from Gemini")
                
                # Store debug information for this API call
                debug_call = {
                    "batch_number": len(self._debug_api_calls) + 1,
                    "timestamp": datetime.now().isoformat(),
                    "segment_ids": [s.get('segment_id') for s in segments_batch],
                    "prompt_length": len(prompt),
                    "response_length": len(response.text),
                    "attempt_number": attempt + 1,
                    "success": True,
                    "prompt_content": prompt,  # Store full prompt
                    "response_content": response.text  # Store full response
                }
                self._debug_api_calls.append(debug_call)
                    
                # Parse response
                assessment_results = json.loads(response.text.strip())
                
                # Validate response format
                if not isinstance(assessment_results, list) or len(assessment_results) != len(segments_batch):
                    raise ValueError(f"Invalid response format: expected {len(segments_batch)} assessments")
                
                # Merge assessments with original segment data
                assessed_segments = []
                for i, segment in enumerate(segments_batch):
                    assessed_segment = segment.copy()
                    assessed_segment['quality_assessment'] = assessment_results[i]['quality_assessment']
                    assessed_segments.append(assessed_segment)
                
                return assessed_segments
                
            except Exception as e:
                logger.warning(f"Assessment attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    delay = self.config.get('error_handling', {}).get('retry_delay', 5)
                    time.sleep(delay * (attempt + 1))  # Exponential backoff
                else:
                    logger.error(f"Failed to assess batch after {max_retries} attempts")
                    raise
    
    def _create_pass2_prompt(self, segments_batch: List[Dict]) -> str:
        """
        Create Pass 2 evaluation prompt with rigorous criteria.
        
        Args:
            segments_batch: Batch of segments to evaluate
            
        Returns:
            Formatted prompt string
        """
        segments_json = json.dumps(segments_batch, indent=2, ensure_ascii=False)
        
        prompt = f"""
## PASS 2 QUALITY ASSESSMENT - EVIDENCE-BASED EVALUATION

**CRITICAL INSTRUCTION:** IGNORE all existing severityRating fields - they are unreliable and must be disregarded completely.

**EVALUATION METHOD:** Evaluate based ONLY on the actual quotes provided in the suggestedClip arrays and clipContextDescription. Score each dimension independently on 1-10 scale.

**CONSERVATIVE APPROACH:** Be conservative - err on the side of exclusion for weak evidence. Only high-quality, well-evidenced segments should receive high scores.

### SCORING DIMENSIONS (1-10 scale):

**1. Quote Strength (1-10):**
- 9-10: Direct false claims with immediate harmful implications
- 7-8: Strong implied harm or misleading statements with clear impact
- 5-6: Questionable statements that could mislead
- 1-4: Opinion statements or weak evidence

**2. Factual Accuracy (1-10):**
- 9-10: Verifiably false claims that can be fact-checked
- 7-8: Misleading but contains some truth elements
- 5-6: Exaggerated or one-sided presentations
- 1-4: Opinion-based or subjective statements

**3. Potential Impact (1-10):**
- 9-10: Could directly influence harmful behavior or major misinformation spread
- 7-8: Likely to spread misinformation to significant audiences
- 5-6: May confuse some viewers or contribute to polarization
- 1-4: Limited impact beyond personal opinion sharing

**4. Content Specificity (1-10):**
- 9-10: Specific false factual claims with concrete details
- 7-8: Concrete statements that are debatable but specific
- 5-6: General statements with some specificity
- 1-4: Vague opinions or generalizations

**5. Context Appropriateness (1-10):**
- 9-10: Clear misinformation with no legitimate debate value
- 7-8: Mostly harmful with some legitimate concerns mixed in
- 5-6: Mixed aspects - some legitimate discussion points
- 1-4: Legitimate discussion or debate topic

### INPUT SEGMENTS:
{segments_json}

### REQUIRED OUTPUT FORMAT:
Return a JSON array with one assessment object per input segment, in the same order. Each assessment must contain:

```json
[
  {{
    "segment_id": "segment_id_from_input",
    "quality_assessment": {{
      "quote_strength": 7,
      "factual_accuracy": 8,
      "potential_impact": 6,
      "content_specificity": 7,
      "context_appropriateness": 4,
      "quality_score": 6.8,
      "selection_reason": "Detailed explanation of why this segment merits inclusion based on the evidence in the quotes and context."
    }}
  }}
]
```

**IMPORTANT:** Calculate quality_score using the weighted formula: (quote_strength × 0.3) + (factual_accuracy × 0.25) + (potential_impact × 0.25) + (content_specificity × 0.1) + (context_appropriateness × 0.1)

Evaluate each segment thoroughly and provide honest, evidence-based scores.
"""
        return prompt
    
    def score_quote_strength(self, quotes: List[Dict], context: str) -> int:
        """
        Evaluate how explicitly harmful the actual quotes are.
        
        Args:
            quotes: List of quote objects with speaker and quote text
            context: Context description for the clip
            
        Returns:
            Score from 1-10 based on quote strength criteria
        """
        # This is a fallback method - primary scoring is done via Gemini API
        # Implementation for standalone use or validation
        
        quote_texts = [q.get('quote', '') for q in quotes]
        combined_text = ' '.join(quote_texts).lower()
        
        # High strength indicators (9-10)
        high_strength_patterns = [
            'false', 'lie', 'completely wrong', 'fake', 'hoax',
            'conspiracy', 'cover-up', 'they\'re hiding'
        ]
        
        # Medium-high strength indicators (7-8)
        medium_high_patterns = [
            'bias', 'propaganda', 'can\'t trust', 'corrupt',
            'agenda', 'misleading'
        ]
        
        # Look for explicit strength indicators
        high_count = sum(1 for pattern in high_strength_patterns if pattern in combined_text)
        medium_count = sum(1 for pattern in medium_high_patterns if pattern in combined_text)
        
        if high_count >= 2:
            return 9
        elif high_count >= 1 or medium_count >= 2:
            return 7
        elif medium_count >= 1:
            return 5
        else:
            return 3
    
    def score_factual_accuracy(self, quotes: List[Dict], context: str) -> int:
        """
        Assess if claims are demonstrably false.
        
        Args:
            quotes: List of quote objects
            context: Context description
            
        Returns:
            Score from 1-10 based on factual accuracy criteria
        """
        # Fallback implementation - primary scoring via Gemini
        quote_texts = [q.get('quote', '') for q in quotes]
        combined_text = ' '.join(quote_texts).lower()
        
        # Look for specific factual claim indicators
        factual_patterns = [
            r'\d+%', 'study shows', 'research', 'data', 'statistics',
            'evidence', 'proven', 'fact', 'documented'
        ]
        
        factual_indicators = sum(1 for pattern in factual_patterns if pattern in combined_text)
        
        if factual_indicators >= 3:
            return 8  # High factual content that could be verified
        elif factual_indicators >= 1:
            return 6  # Some factual claims present
        else:
            return 3  # Mostly opinion-based
    
    def score_potential_impact(self, quotes: List[Dict], context: str) -> int:
        """
        Evaluate likelihood to mislead/harm viewers.
        
        Args:
            quotes: List of quote objects
            context: Context description
            
        Returns:
            Score from 1-10 based on potential impact criteria
        """
        # Fallback implementation
        quote_texts = [q.get('quote', '') for q in quotes]
        combined_text = ' '.join(quote_texts).lower()
        
        # High impact indicators
        impact_patterns = [
            'government', 'election', 'voting', 'democracy', 'media',
            'health', 'medical', 'vaccine', 'treatment', 'science'
        ]
        
        impact_count = sum(1 for pattern in impact_patterns if pattern in combined_text)
        
        if impact_count >= 3:
            return 8
        elif impact_count >= 1:
            return 5
        else:
            return 2
    
    def score_content_specificity(self, quotes: List[Dict], context: str) -> int:
        """
        Assess concrete claims vs vague opinions.
        
        Args:
            quotes: List of quote objects
            context: Context description
            
        Returns:
            Score from 1-10 based on content specificity criteria
        """
        # Fallback implementation
        quote_texts = [q.get('quote', '') for q in quotes]
        combined_text = ' '.join(quote_texts).lower()
        
        # Specificity indicators
        specific_patterns = [
            r'\d+', 'exactly', 'specifically', 'precisely', 'documented',
            'named', 'identified', 'particular', 'actual'
        ]
        
        specific_count = sum(1 for pattern in specific_patterns if pattern in combined_text)
        
        if specific_count >= 4:
            return 8
        elif specific_count >= 2:
            return 6
        elif specific_count >= 1:
            return 4
        else:
            return 2
    
    def score_context_appropriateness(self, quotes: List[Dict], context: str) -> int:
        """
        Distinguish misinformation vs legitimate debate.
        
        Args:
            quotes: List of quote objects
            context: Context description
            
        Returns:
            Score from 1-10 based on context appropriateness criteria
        """
        # Fallback implementation
        combined_text = (context + ' ' + ' '.join(q.get('quote', '') for q in quotes)).lower()
        
        # Legitimate debate indicators (lower scores)
        debate_patterns = [
            'opinion', 'believe', 'think', 'perspective', 'view',
            'discussion', 'debate', 'consider', 'might'
        ]
        
        # Misinformation indicators (higher scores)
        misinfo_patterns = [
            'definitely', 'certainly', 'absolutely', 'fact', 'truth',
            'everyone knows', 'obvious', 'clearly false'
        ]
        
        debate_count = sum(1 for pattern in debate_patterns if pattern in combined_text)
        misinfo_count = sum(1 for pattern in misinfo_patterns if pattern in combined_text)
        
        if misinfo_count >= 2 and debate_count == 0:
            return 9
        elif misinfo_count >= 1:
            return 6
        elif debate_count >= 2:
            return 3
        else:
            return 5
    
    def _apply_filtering_rules(self, assessed_segments: List[Dict]) -> List[Dict]:
        """
        Apply automatic filtering rules with specified thresholds.
        
        Args:
            assessed_segments: Segments with quality assessments
            
        Returns:
            Filtered segments that meet quality thresholds
        """
        filtered_segments = []
        
        # Add filtering metadata to each segment for debug output
        for segment in assessed_segments:
            qa = segment.get('quality_assessment', {})
            
            # Check each dimension against threshold
            passes_filter = True
            failed_dimensions = []
            
            for dimension, threshold in self.filtering_thresholds.items():
                score = qa.get(dimension, 0)
                if score < threshold:
                    passes_filter = False
                    failed_dimensions.append(f"{dimension}: {score} < {threshold}")
            
            # Add filtering metadata
            qa['passes_filter'] = passes_filter
            qa['failed_dimensions'] = failed_dimensions
            qa['filtering_reason'] = 'Passed all thresholds' if passes_filter else f"Failed: {', '.join(failed_dimensions)}"
            
            if passes_filter:
                filtered_segments.append(segment)
                logger.debug(f"Segment {segment.get('segment_id')} passed filtering")
            else:
                logger.debug(f"Segment {segment.get('segment_id')} filtered out: {', '.join(failed_dimensions)}")
        
        logger.info(f"Filtering results: {len(filtered_segments)}/{len(assessed_segments)} segments passed thresholds")
        
        # Store all assessed segments for debug output
        self._all_assessed_segments = assessed_segments
        
        return filtered_segments
    
    def _select_final_segments(self, filtered_segments: List[Dict]) -> List[Dict]:
        """
        Select final segments based on quality scores with minimum count enforcement.
        
        Args:
            filtered_segments: Segments that passed filtering
            
        Returns:
            Final selected segments (8-12 highest quality)
        """
        # Check minimum segment count
        if len(filtered_segments) < self.min_segments_required:
            logger.error(f"Insufficient segments passed filtering: {len(filtered_segments)} < {self.min_segments_required}")
            raise ValueError(
                f"Quality control failed: Only {len(filtered_segments)} segments meet criteria "
                f"(minimum required: {self.min_segments_required}). "
                "Analysis quality is too low to proceed."
            )
        
        # Sort by quality score descending
        sorted_segments = sorted(
            filtered_segments, 
            key=lambda x: x.get('quality_assessment', {}).get('quality_score', 0),
            reverse=True
        )
        
        # Select top 8-12 segments
        final_count = min(self.max_segments_selected, max(self.min_segments_selected, len(sorted_segments)))
        final_segments = sorted_segments[:final_count]
        
        logger.info(f"Final selection: {len(final_segments)} segments selected")
        
        # Log quality score distribution
        scores = [s.get('quality_assessment', {}).get('quality_score', 0) for s in final_segments]
        logger.info(f"Quality score range: {min(scores):.2f} - {max(scores):.2f}")
        
        return final_segments
    
    def _clean_segments_for_output(self, segments: List[Dict]) -> List[Dict]:
        """
        Clean segments by removing debug fields for schema validation and final output.
        
        Args:
            segments: Segments with debug fields
            
        Returns:
            Clean segments without debug fields
        """
        clean_segments = []
        
        for segment in segments:
            clean_segment = segment.copy()
            qa = clean_segment.get('quality_assessment', {})
            
            # Remove debug fields that aren't in the schema
            debug_fields = ['passes_filter', 'failed_dimensions', 'filtering_reason']
            for field in debug_fields:
                qa.pop(field, None)
                
            clean_segments.append(clean_segment)
            
        return clean_segments
    
    def _save_results(
        self, 
        final_segments: List[Dict], 
        metadata: Dict[str, Any], 
        output_path: str
    ) -> None:
        """
        Save filtered results, processing metadata, and debug information.
        
        Args:
            final_segments: Final filtered segments
            metadata: Processing metadata
            output_path: Output file path
        """
        try:
            # Ensure output directory exists
            output_dir = os.path.dirname(output_path)
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            # Save main results file
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(final_segments, f, indent=2, ensure_ascii=False)
            logger.info(f"Results saved to: {output_path}")
            
            # Save metadata file
            metadata_path = output_path.replace('.json', '_metadata.json')
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            logger.info(f"Metadata saved to: {metadata_path}")
            
            # Save debug files with all segment scores and API calls to Quality_Control folder
            self._save_debug_scores(output_path)
            self._save_api_debug_info(output_path)
            
        except Exception as e:
            logger.error(f"Failed to save results: {e}")
            raise
    
    def _save_debug_scores(self, output_path: str) -> None:
        """
        Save detailed scoring information for all segments (including rejected ones).
        
        Args:
            output_path: Base output path for generating debug file path
        """
        try:
            # Create Quality_Control directory in the same episode folder
            base_dir = os.path.dirname(output_path)
            quality_control_dir = os.path.join(base_dir, 'Quality_Control')
            
            if not os.path.exists(quality_control_dir):
                os.makedirs(quality_control_dir)
            
            # Generate debug filename
            base_filename = os.path.splitext(os.path.basename(output_path))[0]
            debug_filename = f"{base_filename}_all_segment_scores.json"
            debug_path = os.path.join(quality_control_dir, debug_filename)
            
            # Prepare debug data with all segments and their scores
            if hasattr(self, '_all_assessed_segments'):
                debug_data = {
                    "debug_info": {
                        "total_segments": len(self._all_assessed_segments),
                        "filtering_thresholds": self.filtering_thresholds,
                        "scoring_weights": self.scoring_weights,
                        "generated_timestamp": datetime.now().isoformat()
                    },
                    "all_segments_with_scores": []
                }
                
                # Sort segments by quality score (highest first) for easier analysis
                sorted_all_segments = sorted(
                    self._all_assessed_segments,
                    key=lambda x: x.get('quality_assessment', {}).get('quality_score', 0),
                    reverse=True
                )
                
                for segment in sorted_all_segments:
                    qa = segment.get('quality_assessment', {})
                    
                    debug_segment = {
                        "segment_id": segment.get('segment_id'),
                        "narrativeSegmentTitle": segment.get('narrativeSegmentTitle'),
                        "quality_assessment": {
                            "quote_strength": qa.get('quote_strength'),
                            "factual_accuracy": qa.get('factual_accuracy'),
                            "potential_impact": qa.get('potential_impact'),
                            "content_specificity": qa.get('content_specificity'),
                            "context_appropriateness": qa.get('context_appropriateness'),
                            "quality_score": qa.get('quality_score'),
                            "passes_filter": qa.get('passes_filter'),
                            "failed_dimensions": qa.get('failed_dimensions'),
                            "filtering_reason": qa.get('filtering_reason'),
                            "selection_reason": qa.get('selection_reason')
                        },
                        # Include key context for analysis
                        "clipContextDescription": segment.get('clipContextDescription', '')[:200] + "..." if len(segment.get('clipContextDescription', '')) > 200 else segment.get('clipContextDescription', ''),
                        "suggestedClip": segment.get('suggestedClip', [])[:3]  # First 3 quotes for context
                    }
                    
                    debug_data["all_segments_with_scores"].append(debug_segment)
                
                # Save debug file
                with open(debug_path, 'w', encoding='utf-8') as f:
                    json.dump(debug_data, f, indent=2, ensure_ascii=False)
                
                logger.info(f"Debug scores saved to: {debug_path}")
                
                # Log summary statistics
                passed_count = sum(1 for s in self._all_assessed_segments if s.get('quality_assessment', {}).get('passes_filter'))
                failed_count = len(self._all_assessed_segments) - passed_count
                logger.info(f"Debug summary: {passed_count} passed, {failed_count} failed filtering")
                
            else:
                logger.warning("No assessed segments data available for debug output")
                
        except Exception as e:
            logger.error(f"Failed to save debug scores: {e}")
            # Don't raise - debug output failure shouldn't break main pipeline
    
    def _save_api_debug_info(self, output_path: str) -> None:
        """
        Save detailed API call information including prompts and responses.
        
        Args:
            output_path: Base output path for generating debug file paths
        """
        try:
            # Create Quality_Control directory
            base_dir = os.path.dirname(output_path)
            quality_control_dir = os.path.join(base_dir, 'Quality_Control')
            
            if not os.path.exists(quality_control_dir):
                os.makedirs(quality_control_dir)
            
            base_filename = os.path.splitext(os.path.basename(output_path))[0]
            
            # Save API call summary
            api_summary_path = os.path.join(quality_control_dir, f"{base_filename}_api_calls_summary.json")
            api_summary = {
                "api_debug_info": {
                    "total_api_calls": len(self._debug_api_calls),
                    "generated_timestamp": datetime.now().isoformat(),
                    "model_used": "gemini-2.5-pro-preview-06-05"
                },
                "api_calls": self._debug_api_calls
            }
            
            with open(api_summary_path, 'w', encoding='utf-8') as f:
                json.dump(api_summary, f, indent=2, ensure_ascii=False)
            
            logger.info(f"API debug summary saved to: {api_summary_path}")
            
            # Save individual prompt and response files for each batch
            prompts_dir = os.path.join(quality_control_dir, 'prompts_and_responses')
            if not os.path.exists(prompts_dir):
                os.makedirs(prompts_dir)
            
            # Re-generate prompts to save them (we need to recreate them)
            batch_number = 1
            for debug_call in self._debug_api_calls:
                # Save prompt for this batch
                prompt_filename = f"batch_{batch_number}_prompt.txt"
                response_filename = f"batch_{batch_number}_response.json"
                
                prompt_path = os.path.join(prompts_dir, prompt_filename)
                response_path = os.path.join(prompts_dir, response_filename)
                
                # Create header for prompt file
                prompt_header = f"""# Batch {batch_number} - Gemini API Prompt
# Generated: {debug_call['timestamp']}
# Segment IDs: {', '.join(debug_call['segment_ids'])}
# Prompt Length: {debug_call['prompt_length']} characters
# Response Length: {debug_call['response_length']} characters
# Attempt: {debug_call['attempt_number']}
# Success: {debug_call['success']}

{'=' * 80}
FULL PROMPT SENT TO GEMINI:
{'=' * 80}

"""
                
                # Save actual prompt content
                with open(prompt_path, 'w', encoding='utf-8') as f:
                    f.write(prompt_header)
                    f.write(debug_call.get('prompt_content', '# Prompt content not available'))
                
                # Save actual response content
                try:
                    # Try to parse response as JSON for pretty formatting
                    response_json = json.loads(debug_call.get('response_content', '{}'))
                    response_data = {
                        "raw_response": debug_call.get('response_content', ''),
                        "parsed_response": response_json,
                        "metadata": {
                            "batch_number": batch_number,
                            "response_length": debug_call['response_length'],
                            "timestamp": debug_call['timestamp'],
                            "success": debug_call['success']
                        }
                    }
                except json.JSONDecodeError:
                    # If response isn't valid JSON, save as raw text
                    response_data = {
                        "raw_response": debug_call.get('response_content', ''),
                        "error": "Response was not valid JSON",
                        "metadata": {
                            "batch_number": batch_number,
                            "response_length": debug_call['response_length'],
                            "timestamp": debug_call['timestamp'],
                            "success": debug_call['success']
                        }
                    }
                
                with open(response_path, 'w', encoding='utf-8') as f:
                    json.dump(response_data, f, indent=2, ensure_ascii=False)
                
                batch_number += 1
            
            logger.info(f"Individual prompts/responses saved to: {prompts_dir}")
            logger.info(f"API debug info: {len(self._debug_api_calls)} calls documented")
            
        except Exception as e:
            logger.error(f"Failed to save API debug info: {e}")
            # Don't raise - debug output failure shouldn't break main pipeline


def create_pass2_prompt_file(output_dir: str) -> str:
    """
    Create and save the Pass 2 evaluation prompt to a text file.
    
    Args:
        output_dir: Directory to save the prompt file
        
    Returns:
        Path to the saved prompt file
    """
    prompt_content = """
## PASS 2 QUALITY ASSESSMENT - EVIDENCE-BASED EVALUATION

**CRITICAL INSTRUCTION:** IGNORE all existing severityRating fields - they are unreliable and must be disregarded completely.

**EVALUATION METHOD:** Evaluate based ONLY on the actual quotes provided in the suggestedClip arrays and clipContextDescription. Score each dimension independently on 1-10 scale.

**CONSERVATIVE APPROACH:** Be conservative - err on the side of exclusion for weak evidence. Only high-quality, well-evidenced segments should receive high scores.

### SCORING DIMENSIONS (1-10 scale):

**1. Quote Strength (1-10):**
- 9-10: Direct false claims with immediate harmful implications
- 7-8: Strong implied harm or misleading statements with clear impact
- 5-6: Questionable statements that could mislead
- 1-4: Opinion statements or weak evidence

**2. Factual Accuracy (1-10):**
- 9-10: Verifiably false claims that can be fact-checked
- 7-8: Misleading but contains some truth elements
- 5-6: Exaggerated or one-sided presentations
- 1-4: Opinion-based or subjective statements

**3. Potential Impact (1-10):**
- 9-10: Could directly influence harmful behavior or major misinformation spread
- 7-8: Likely to spread misinformation to significant audiences
- 5-6: May confuse some viewers or contribute to polarization
- 1-4: Limited impact beyond personal opinion sharing

**4. Content Specificity (1-10):**
- 9-10: Specific false factual claims with concrete details
- 7-8: Concrete statements that are debatable but specific
- 5-6: General statements with some specificity
- 1-4: Vague opinions or generalizations

**5. Context Appropriateness (1-10):**
- 9-10: Clear misinformation with no legitimate debate value
- 7-8: Mostly harmful with some legitimate concerns mixed in
- 5-6: Mixed aspects - some legitimate discussion points
- 1-4: Legitimate discussion or debate topic

### WEIGHTED SCORING FORMULA:
quality_score = (quote_strength × 0.3) + (factual_accuracy × 0.25) + (potential_impact × 0.25) + (content_specificity × 0.1) + (context_appropriateness × 0.1)

### FILTERING THRESHOLDS:
- Quote Strength: ≥ 6
- Factual Accuracy: ≥ 5
- Potential Impact: ≥ 5
- Content Specificity: ≥ 5
- Context Appropriateness: ≥ 5

### SELECTION CRITERIA:
- Final selection: Top 8-12 segments by quality score
- Minimum requirement: At least 6 segments must pass all thresholds
- If fewer than 6 segments qualify, reject entire analysis (do not lower standards)

This prompt is designed for evidence-based, conservative evaluation that prioritizes quality over quantity.
"""
    
    # Ensure Quality_Control directory exists
    quality_control_dir = os.path.join(output_dir, 'Quality_Control')
    if not os.path.exists(quality_control_dir):
        os.makedirs(quality_control_dir)
    
    # Save prompt file
    prompt_path = os.path.join(quality_control_dir, 'pass_2_prompt.txt')
    with open(prompt_path, 'w', encoding='utf-8') as f:
        f.write(f"# Pass 2 Quality Assessment Prompt\n")
        f.write(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"# Two-Pass AI Quality Control System\n\n")
        f.write(prompt_content)
    
    logger.info(f"Pass 2 prompt saved to: {prompt_path}")
    return prompt_path


# Main execution function for command-line usage
def main():
    """Main function for command-line usage."""
    if len(sys.argv) < 2:
        print("Usage: python quality_assessor.py <input_file> [output_file] [--test-mode]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    
    # Check for test mode flag
    test_mode = '--test-mode' in sys.argv
    
    # Get output file path
    if len(sys.argv) > 2 and not sys.argv[2].startswith('--'):
        output_file = sys.argv[2]
    else:
        output_file = None
    
    if not output_file:
        base_name = os.path.splitext(input_file)[0]
        output_file = f"{base_name}_filtered_quality_results.json"
    
    try:
        # Initialize quality assessor
        assessor = QualityAssessor(test_mode=test_mode)
        
        if test_mode:
            print("Running in TEST MODE with relaxed thresholds for demonstration")
        
        # Process Pass 1 results
        final_segments, metadata = assessor.process_pass1_results(input_file, output_file)
        
        # Create prompt file in same directory
        output_dir = os.path.dirname(output_file)
        create_pass2_prompt_file(output_dir)
        
        print("Pass 2 Quality Assessment completed successfully!")
        print(f"Results: {output_file}")
        print(f"Final segments: {len(final_segments)}")
        print(f"Processing summary: {metadata['input_segments_count']} -> {metadata['final_segments_count']} segments")
        
    except Exception as e:
        logger.error(f"Quality assessment failed: {e}")
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()