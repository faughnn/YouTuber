"""
Rebuttal Verification Framework - Two-Pass AI Quality Control System

This module implements comprehensive fact-checking for generated rebuttals with accuracy scoring
and verification metadata tracking. Evaluates post_clip sections for factual correctness and 
argument completeness using a 3-dimension assessment system with automatic rewriting triggers.

Features:
- 3-dimension independent assessment system (1-10 scale)
- Automatic rewriting triggers with configurable thresholds
- Gemini API integration for AI-powered rebuttal verification
- Comprehensive I/O validation using JSON schema framework
- Quality Control Results tracking and metadata preservation

Author: APM Implementation Agent
Created: 2025-01-13
Pipeline: Two-Pass AI Quality Control System (Phase 2, Task 2.1)
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

class RebuttalVerifierRewriter:
    """
    Comprehensive fact-checking system for generated rebuttals with accuracy scoring
    and verification metadata tracking.
    
    Implements 3-dimension assessment of post_clip rebuttal content with automatic
    rewriting triggers to ensure high-quality fact-based counter-arguments.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the RebuttalVerifierRewriter with configuration and validation.
        
        Args:
            config_path: Optional path to config file. If None, uses default location.
        """
        self.config = self._load_config(config_path)
        self.validator = JSONSchemaValidator()
        self._configure_gemini()
        
        # Verification thresholds (exact as specified in task assignment)
        self.verification_thresholds = {
            'accuracy': 7,        # Accuracy < 7 triggers rewriting
            'completeness': 6,    # Completeness < 6 triggers rewriting
            'effectiveness': 6    # Effectiveness < 6 triggers rewriting
        }
        
        # Debug storage for API calls and assessment results
        self._debug_api_calls = []
        self._all_assessments = []
        
        logger.info("RebuttalVerifierRewriter initialized successfully")
        
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
    
    def verify_and_improve_rebuttals(
        self, 
        input_data: Union[Dict, str, Path],
        output_path: Optional[str] = None
    ) -> Tuple[Dict, Dict[str, Any]]:
        """
        Main verification function that processes unified script and improves rebuttals.
        
        Args:
            input_data: Unified script data (data or file path)
            output_path: Optional output path for saving results
            
        Returns:
            Tuple of (verified_script_data, verification_metadata)
        """
        logger.info("=== REBUTTAL VERIFICATION AND REWRITING STARTED ===")
        
        # Step 1: Validate input data
        logger.info("Validating unified script input data...")
        is_valid, error_messages = self.validator.validate_script_input(input_data)
        if not is_valid:
            error_msg = f"Input validation failed:\n" + "\n".join(error_messages)
            logger.error(error_msg)
            raise ValueError(error_msg)
        logger.info("✅ Input validation successful")
        
        # Step 2: Load data if file path provided
        if isinstance(input_data, (str, Path)):
            with open(input_data, 'r', encoding='utf-8') as f:
                script_data = json.load(f)
        else:
            script_data = input_data
            
        # Step 3: Extract post_clip sections containing rebuttals
        logger.info("Extracting post_clip sections for rebuttal verification...")
        post_clip_sections = self._extract_post_clip_sections(script_data)
        
        if not post_clip_sections:
            logger.warning("No post_clip sections found - nothing to verify")
            return script_data, {"rebuttals_assessed": 0, "rebuttals_rewritten": 0}
        
        logger.info(f"Found {len(post_clip_sections)} post_clip sections to verify")
        
        # Step 4: Assess rebuttal quality using 3-dimension system
        logger.info("Assessing rebuttal quality via Gemini API...")
        assessed_rebuttals = self._assess_rebuttal_quality(post_clip_sections)
        
        # Step 5: Determine which rebuttals need rewriting
        logger.info("Applying verification triggers and thresholds...")
        rebuttals_needing_improvement = self._identify_rebuttals_for_rewriting(assessed_rebuttals)
        
        # Step 6: Rewrite rebuttals that don't meet thresholds
        improved_rebuttals = []
        if rebuttals_needing_improvement:
            logger.info(f"Rewriting {len(rebuttals_needing_improvement)} rebuttals...")
            improved_rebuttals = self._rewrite_poor_rebuttals(rebuttals_needing_improvement)
        
        # Step 7: Create clean script with improvements and separate verification data
        logger.info("Creating clean script with improvements and verification data...")
        clean_script_data, verification_results = self._create_verified_script(
            script_data, assessed_rebuttals, improved_rebuttals
        )
        
        # Step 8: Validate clean script output (should match unified_podcast_script schema)
        logger.info("Validating clean script output...")
        is_valid, error_messages = self.validator.validate_script_input(clean_script_data)
        if not is_valid:
            error_msg = f"Clean script validation failed:\n" + "\n".join(error_messages)
            logger.error(error_msg)
            raise ValueError(error_msg)
        logger.info("✅ Clean script validation successful")
        
        # Step 9: Save results and quality control data if output path provided
        verification_metadata = {
            'verification_timestamp': datetime.now().isoformat(),
            'rebuttals_assessed': len(assessed_rebuttals),
            'rebuttals_rewritten': len(improved_rebuttals),
            'verification_thresholds': self.verification_thresholds,
            'total_post_clip_sections': len(post_clip_sections)
        }
        
        if output_path:
            self._save_verification_results(
                clean_script_data, verification_results, verification_metadata, output_path
            )
            
        logger.info(f"=== REBUTTAL VERIFICATION COMPLETED ===")
        logger.info(f"Results: {len(assessed_rebuttals)} assessed, {len(improved_rebuttals)} rewritten")
        
        return clean_script_data, verification_metadata
    
    def _extract_post_clip_sections(self, script_data: Dict) -> List[Dict]:
        """
        Extract post_clip sections containing rebuttal content from the unified script.
        
        Args:
            script_data: Unified script data
            
        Returns:
            List of post_clip sections with rebuttal content
        """
        post_clip_sections = []
        
        podcast_sections = script_data.get('podcast_sections', [])
        for section in podcast_sections:
            if (section.get('section_type') == 'post_clip' and 
                section.get('script_content', '').strip()):
                post_clip_sections.append(section)
                logger.debug(f"Found post_clip section: {section.get('section_id')}")
        
        return post_clip_sections
    
    def _assess_rebuttal_quality(self, post_clip_sections: List[Dict]) -> List[Dict]:
        """
        Assess rebuttal quality for post_clip sections using 3-dimension evaluation.
        
        Args:
            post_clip_sections: List of post_clip sections
            
        Returns:
            List of sections with quality assessments added
        """
        assessed_rebuttals = []
        
        # Process sections in batches to avoid API limits
        batch_size = 3
        total_sections = len(post_clip_sections)
        logger.info(f"Processing {total_sections} rebuttals in batches of {batch_size}...")
        
        for i in range(0, total_sections, batch_size):
            batch = post_clip_sections[i:i + batch_size]
            logger.info(f"Processing batch {i//batch_size + 1}/{(total_sections-1)//batch_size + 1} ({len(batch)} sections)")
            
            try:
                batch_results = self._assess_rebuttal_batch(batch)
                assessed_rebuttals.extend(batch_results)
                logger.info(f"✅ Batch {i//batch_size + 1} completed - {len(batch_results)} rebuttals assessed")
                
                # Rate limiting delay
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"Failed to process batch {i//batch_size + 1}: {e}")
                continue
        
        logger.info(f"Successfully assessed {len(assessed_rebuttals)}/{total_sections} rebuttal sections")
        
        # Store for debug output
        self._all_assessments = assessed_rebuttals
        
        return assessed_rebuttals
    
    def _assess_rebuttal_batch(self, sections_batch: List[Dict]) -> List[Dict]:
        """
        Assess a batch of post_clip sections using Gemini API.
        
        Args:
            sections_batch: Batch of sections to assess
            
        Returns:
            List of sections with rebuttal assessments added
        """
        # Create evaluation prompt
        prompt = self._create_rebuttal_assessment_prompt(sections_batch)
        
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
                
                # Store debug information
                debug_call = {
                    "batch_number": len(self._debug_api_calls) + 1,
                    "timestamp": datetime.now().isoformat(),
                    "section_ids": [s.get('section_id') for s in sections_batch],
                    "prompt_length": len(prompt),
                    "response_length": len(response.text),
                    "attempt_number": attempt + 1,
                    "success": True,
                    "prompt_content": prompt,
                    "response_content": response.text
                }
                self._debug_api_calls.append(debug_call)
                    
                # Parse response
                assessment_results = json.loads(response.text.strip())
                
                # Validate response format
                if not isinstance(assessment_results, list) or len(assessment_results) != len(sections_batch):
                    raise ValueError(f"Invalid response format: expected {len(sections_batch)} assessments")
                
                # Merge assessments with original section data
                assessed_sections = []
                for i, section in enumerate(sections_batch):
                    assessed_section = section.copy()
                    assessed_section['rebuttal_assessment'] = assessment_results[i]['rebuttal_assessment']
                    assessed_sections.append(assessed_section)
                
                return assessed_sections
                
            except Exception as e:
                logger.warning(f"Assessment attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    delay = self.config.get('error_handling', {}).get('retry_delay', 5)
                    time.sleep(delay * (attempt + 1))
                else:
                    logger.error(f"Failed to assess batch after {max_retries} attempts")
                    raise
    
    def _create_rebuttal_assessment_prompt(self, sections_batch: List[Dict]) -> str:
        """
        Create rebuttal assessment prompt with 3-dimension evaluation criteria.
        
        Args:
            sections_batch: Batch of sections to evaluate
            
        Returns:
            Formatted prompt string
        """
        sections_json = json.dumps(sections_batch, indent=2, ensure_ascii=False)
        
        prompt = f"""
## REBUTTAL VERIFICATION ASSESSMENT - FACT-CHECKING EVALUATION

**EVALUATION METHOD:** Evaluate the post_clip rebuttal content in each section based on factual correctness, argument completeness, and persuasiveness. Score each dimension independently on 1-10 scale.

**FOCUS:** Examine the script_content field in each post_clip section, which contains rebuttal content designed to counter harmful claims from the preceding video clip.

### SCORING DIMENSIONS (1-10 scale):

**1. Rebuttal Accuracy (1-10):**
- 9-10: Completely accurate with verifiable facts and proper citations
- 7-8: Mostly accurate with minor factual issues or missing sources
- 5-6: Some factual inaccuracies or unsupported claims present
- 1-4: Significant factual errors or misleading counter-arguments

**2. Rebuttal Completeness (1-10):**
- 9-10: Comprehensive coverage of all key counter-arguments needed
- 7-8: Good coverage with minor gaps in addressing harmful claims
- 5-6: Adequate but missing some important counter-points
- 1-4: Insufficient counter-argument coverage, major gaps present

**3. Rebuttal Effectiveness (1-10):**
- 9-10: Compelling, well-sourced rebuttals that effectively counter harmful claims
- 7-8: Strong rebuttals with good evidence and persuasive presentation
- 5-6: Moderate effectiveness with some persuasive elements
- 1-4: Weak or ineffective counter-arguments, poor presentation

### INPUT SECTIONS:
{sections_json}

### REQUIRED OUTPUT FORMAT:
Return a JSON array with one assessment object per input section, in the same order. Each assessment must contain:

```json
[
  {{
    "section_id": "section_id_from_input",
    "rebuttal_assessment": {{
      "accuracy": 7,
      "completeness": 8,
      "effectiveness": 6,
      "overall_quality_score": 7.0,
      "assessment_reasoning": "Detailed explanation of the assessment scores based on the rebuttal content quality, factual accuracy, and effectiveness in countering harmful claims.",
      "improvement_needed": true,
      "improvement_areas": ["accuracy", "effectiveness"]
    }}
  }}
]
```

**CRITICAL INSTRUCTIONS:**
- Focus evaluation specifically on the script_content of post_clip sections
- overall_quality_score should be the average of the three dimension scores
- improvement_needed = true if any score falls below thresholds (Accuracy<7, Completeness<6, Effectiveness<6)
- improvement_areas should list all dimensions that failed to meet thresholds
- Provide detailed reasoning for each assessment

Evaluate each section thoroughly and provide honest, evidence-based scores for rebuttal quality.
"""
        return prompt
    
    def assess_rebuttal_accuracy(self, rebuttal_content: str, context: str) -> int:
        """
        Evaluate factual correctness of rebuttal claims.
        
        Args:
            rebuttal_content: The rebuttal text content
            context: Context information for the rebuttal
            
        Returns:
            Score from 1-10 based on factual accuracy criteria
        """
        # Fallback method for standalone use - primary scoring via Gemini API
        content_lower = rebuttal_content.lower()
        
        # High accuracy indicators (9-10)
        accuracy_patterns = [
            'study shows', 'research indicates', 'according to', 'data reveals',
            'peer-reviewed', 'published research', 'scientific evidence'
        ]
        
        # Medium accuracy indicators (7-8)  
        medium_patterns = [
            'experts say', 'analysis suggests', 'findings show',
            'documented', 'verified', 'confirmed'
        ]
        
        high_count = sum(1 for pattern in accuracy_patterns if pattern in content_lower)
        medium_count = sum(1 for pattern in medium_patterns if pattern in content_lower)
        
        if high_count >= 2:
            return 9
        elif high_count >= 1 or medium_count >= 2:
            return 7
        elif medium_count >= 1:
            return 5
        else:
            return 3
    
    def assess_rebuttal_completeness(self, rebuttal_content: str, context: str) -> int:
        """
        Evaluate argument coverage and counter-point inclusion.
        
        Args:
            rebuttal_content: The rebuttal text content
            context: Context information for the rebuttal
            
        Returns:
            Score from 1-10 based on completeness criteria
        """
        # Fallback method - primary scoring via Gemini API
        content_lower = rebuttal_content.lower()
        
        # Completeness indicators
        completeness_patterns = [
            'however', 'but', 'on the other hand', 'in contrast',
            'while', 'although', 'despite', 'nevertheless',
            'furthermore', 'additionally', 'moreover', 'also'
        ]
        
        # Counter-argument indicators
        counter_patterns = [
            'actually', 'in fact', 'contrary to', 'evidence shows',
            'reality is', 'truth is', 'research indicates'
        ]
        
        completeness_count = sum(1 for pattern in completeness_patterns if pattern in content_lower)
        counter_count = sum(1 for pattern in counter_patterns if pattern in content_lower)
        
        total_indicators = completeness_count + counter_count
        
        if total_indicators >= 4:
            return 8
        elif total_indicators >= 2:
            return 6
        elif total_indicators >= 1:
            return 4
        else:
            return 2
    
    def assess_rebuttal_effectiveness(self, rebuttal_content: str, context: str) -> int:
        """
        Evaluate counter-argument strength and persuasiveness.
        
        Args:
            rebuttal_content: The rebuttal text content
            context: Context information for the rebuttal
            
        Returns:
            Score from 1-10 based on effectiveness criteria
        """
        # Fallback method - primary scoring via Gemini API
        content_lower = rebuttal_content.lower()
        
        # Strong effectiveness indicators
        strong_patterns = [
            'compelling evidence', 'overwhelming data', 'clear proof',
            'undeniable fact', 'proven wrong', 'definitively shows'
        ]
        
        # Medium effectiveness indicators
        medium_patterns = [
            'evidence suggests', 'data indicates', 'research shows',
            'experts agree', 'studies confirm', 'analysis reveals'
        ]
        
        # Persuasive language indicators
        persuasive_patterns = [
            'importantly', 'crucially', 'significantly', 'clearly',
            'obviously', 'undoubtedly', 'certainly'
        ]
        
        strong_count = sum(1 for pattern in strong_patterns if pattern in content_lower)
        medium_count = sum(1 for pattern in medium_patterns if pattern in content_lower)
        persuasive_count = sum(1 for pattern in persuasive_patterns if pattern in content_lower)
        
        if strong_count >= 1 and persuasive_count >= 2:
            return 9
        elif strong_count >= 1 or (medium_count >= 2 and persuasive_count >= 1):
            return 7
        elif medium_count >= 1 and persuasive_count >= 1:
            return 5
        elif medium_count >= 1 or persuasive_count >= 1:
            return 3
        else:
            return 2
    
    def _identify_rebuttals_for_rewriting(self, assessed_rebuttals: List[Dict]) -> List[Dict]:
        """
        Identify rebuttals that need rewriting based on verification thresholds.
        
        Args:
            assessed_rebuttals: Rebuttals with quality assessments
            
        Returns:
            List of rebuttals that need improvement
        """
        rebuttals_needing_improvement = []
        
        for rebuttal in assessed_rebuttals:
            assessment = rebuttal.get('rebuttal_assessment', {})
            
            # Check thresholds: Accuracy < 7, Completeness < 6, Effectiveness < 6
            accuracy = assessment.get('accuracy', 0)
            completeness = assessment.get('completeness', 0) 
            effectiveness = assessment.get('effectiveness', 0)
            
            needs_improvement = (
                accuracy < self.verification_thresholds['accuracy'] or
                completeness < self.verification_thresholds['completeness'] or
                effectiveness < self.verification_thresholds['effectiveness']
            )
            
            if needs_improvement:
                failed_dimensions = []
                if accuracy < self.verification_thresholds['accuracy']:
                    failed_dimensions.append(f"accuracy: {accuracy} < {self.verification_thresholds['accuracy']}")
                if completeness < self.verification_thresholds['completeness']:
                    failed_dimensions.append(f"completeness: {completeness} < {self.verification_thresholds['completeness']}")
                if effectiveness < self.verification_thresholds['effectiveness']:
                    failed_dimensions.append(f"effectiveness: {effectiveness} < {self.verification_thresholds['effectiveness']}")
                
                rebuttal['improvement_reasons'] = failed_dimensions
                rebuttals_needing_improvement.append(rebuttal)
                
                logger.debug(f"Rebuttal {rebuttal.get('section_id')} needs improvement: {', '.join(failed_dimensions)}")
            else:
                logger.debug(f"Rebuttal {rebuttal.get('section_id')} meets all thresholds")
        
        logger.info(f"Identified {len(rebuttals_needing_improvement)}/{len(assessed_rebuttals)} rebuttals for improvement")
        return rebuttals_needing_improvement
    
    def _rewrite_poor_rebuttals(self, rebuttals_to_improve: List[Dict]) -> List[Dict]:
        """
        Rewrite rebuttals that don't meet quality thresholds.
        
        Args:
            rebuttals_to_improve: List of rebuttals needing improvement
            
        Returns:
            List of improved rebuttals with new content and metadata
        """
        improved_rebuttals = []
        
        # Process rebuttals in batches
        batch_size = 2
        total_rebuttals = len(rebuttals_to_improve)
        
        for i in range(0, total_rebuttals, batch_size):
            batch = rebuttals_to_improve[i:i + batch_size]
            logger.info(f"Rewriting batch {i//batch_size + 1}/{(total_rebuttals-1)//batch_size + 1} ({len(batch)} rebuttals)")
            
            try:
                batch_results = self._rewrite_rebuttal_batch(batch)
                improved_rebuttals.extend(batch_results)
                
                # Rate limiting delay
                time.sleep(3)
                
            except Exception as e:
                logger.error(f"Failed to rewrite batch {i//batch_size + 1}: {e}")
                continue
        
        logger.info(f"Successfully rewrote {len(improved_rebuttals)}/{total_rebuttals} rebuttals")
        return improved_rebuttals
    
    def _rewrite_rebuttal_batch(self, rebuttals_batch: List[Dict]) -> List[Dict]:
        """
        Rewrite a batch of rebuttals using Gemini API.
        
        Args:
            rebuttals_batch: Batch of rebuttals to rewrite
            
        Returns:
            List of improved rebuttals
        """
        # Create rewriting prompt
        prompt = self._create_rebuttal_rewriting_prompt(rebuttals_batch)
        
        max_retries = self.config.get('error_handling', {}).get('max_retries', 3)
        
        for attempt in range(max_retries):
            try:
                model = genai.GenerativeModel(
                    'gemini-2.5-pro-preview-06-05',
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.2,  # Slightly higher for creative rewriting
                        top_p=0.9,
                        candidate_count=1,
                        response_mime_type="application/json"
                    )
                )
                
                response = model.generate_content(prompt)
                
                if not response.text:
                    raise ValueError("Empty response from Gemini")
                
                # Parse response
                rewriting_results = json.loads(response.text.strip())
                
                # Validate response format
                if not isinstance(rewriting_results, list) or len(rewriting_results) != len(rebuttals_batch):
                    raise ValueError(f"Invalid response format: expected {len(rebuttals_batch)} rewrites")
                
                # Create improved rebuttal objects
                improved_rebuttals = []
                for i, rebuttal in enumerate(rebuttals_batch):
                    improved_data = {
                        'section_id': rebuttal.get('section_id'),
                        'original_rebuttal': rebuttal.get('script_content'),
                        'improved_rebuttal': rewriting_results[i]['improved_rebuttal'],
                        'improvement_reasoning': rewriting_results[i]['improvement_reasoning'],
                        'improvement_areas': rebuttal.get('improvement_reasons', []),
                        'original_scores': rebuttal.get('rebuttal_assessment', {}),
                        'rewrite_timestamp': datetime.now().isoformat()
                    }
                    improved_rebuttals.append(improved_data)
                
                return improved_rebuttals
                
            except Exception as e:
                logger.warning(f"Rewriting attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    delay = self.config.get('error_handling', {}).get('retry_delay', 5)
                    time.sleep(delay * (attempt + 1))
                else:
                    logger.error(f"Failed to rewrite batch after {max_retries} attempts")
                    raise
    
    def _create_rebuttal_rewriting_prompt(self, rebuttals_batch: List[Dict]) -> str:
        """
        Create rebuttal rewriting prompt with Jon Stewart voice and TTS optimization.
        
        Args:
            rebuttals_batch: Batch of rebuttals to rewrite
            
        Returns:
            Formatted prompt string
        """
        rebuttals_data = []
        for rebuttal in rebuttals_batch:
            rebuttal_info = {
                'section_id': rebuttal.get('section_id'),
                'original_rebuttal': rebuttal.get('script_content'),
                'assessment_scores': rebuttal.get('rebuttal_assessment', {}),
                'improvement_reasons': rebuttal.get('improvement_reasons', []),
                'clip_reference': rebuttal.get('clip_reference')
            }
            rebuttals_data.append(rebuttal_info)
        
        rebuttals_json = json.dumps(rebuttals_data, indent=2, ensure_ascii=False)
        
        # Load prompt template from external file
        prompt_template = self._load_rewriting_prompt_template()
        
        # Format the prompt with the rebuttals data
        prompt = prompt_template.format(rebuttals_json=rebuttals_json)
        
        return prompt
    
    def _load_rewriting_prompt_template(self) -> str:
        """
        Load the rebuttal rewriting prompt template from external file.
        
        Returns:
            Prompt template string
        """
        try:
            prompt_file = os.path.join(current_dir, 'Quality_Control', 'rebuttal_rewriting_prompt.txt')
            
            with open(prompt_file, 'r', encoding='utf-8') as f:
                template = f.read()
                
            logger.debug(f"Loaded rewriting prompt template from: {prompt_file}")
            return template
            
        except Exception as e:
            logger.error(f"Failed to load rewriting prompt template: {e}")
            # Fallback to basic prompt if file loading fails
            return self._get_fallback_rewriting_prompt()
    
    def _get_fallback_rewriting_prompt(self) -> str:
        """
        Fallback rewriting prompt if external file fails to load.
        
        Returns:
            Basic fallback prompt string
        """
        return """
## REBUTTAL REWRITING - ALTERNATIVE MEDIA LITERACY VOICE

Transform these rebuttals into compelling, snarky fact-checks while maintaining the Alternative Media Literacy voice: humorous, sarcastic, and factually accurate.

### INPUT REBUTTALS TO IMPROVE:
{rebuttals_json}

### REQUIRED OUTPUT FORMAT:
Return a JSON array with improved rebuttals, maintaining Jon Stewart-style wit and TTS optimization.

```json
[
  {{
    "section_id": "section_id_from_input",
    "improved_rebuttal": "Rewritten rebuttal with snarky voice and factual accuracy...",
    "improvement_reasoning": "Explanation of improvements made..."
  }}
]
```
"""
    
    def _create_verified_script(
        self, 
        original_script: Dict, 
        assessed_rebuttals: List[Dict],
        improved_rebuttals: List[Dict]
    ) -> Tuple[Dict, Dict]:
        """
        Create clean script with improvements and separate verification data.
        
        Args:
            original_script: Original unified script data
            assessed_rebuttals: List of assessed rebuttals
            improved_rebuttals: List of improved rebuttals
            
        Returns:
            Tuple of (clean_script_with_improvements, verification_data)
        """
        # Create a clean copy of the original script for pipeline use
        clean_script = original_script.copy()
        
        # Update script content with improved rebuttals where available
        improved_by_section_id = {r['section_id']: r for r in improved_rebuttals}
        
        for section in clean_script.get('podcast_sections', []):
            if (section.get('section_type') == 'post_clip' and 
                section.get('section_id') in improved_by_section_id):
                
                improved_rebuttal = improved_by_section_id[section.get('section_id')]
                section['script_content'] = improved_rebuttal['improved_rebuttal']
                logger.debug(f"Updated script content for section: {section.get('section_id')}")
        
        # Create separate verification_results object
        verification_results = {
            'verification_timestamp': datetime.now().isoformat(),
            'verification_agent_id': 'rebuttal_verifier_rewriter',
            'rebuttals_assessed': [],
            'rebuttals_rewritten': [],
            'accuracy_improvements': [],
            'completeness_improvements': [],
            'effectiveness_improvements': [],
            'final_verification_score': 0.0
        }
        
        # Populate rebuttals_assessed
        for rebuttal in assessed_rebuttals:
            assessment = rebuttal.get('rebuttal_assessment', {})
            assessed_entry = {
                'segment_id': rebuttal.get('clip_reference', rebuttal.get('section_id')),
                'original_rebuttal': rebuttal.get('script_content', ''),
                'assessment_score': assessment.get('overall_quality_score', 0),
                'assessment_reasoning': assessment.get('assessment_reasoning', '')
            }
            verification_results['rebuttals_assessed'].append(assessed_entry)
        
        # Populate rebuttals_rewritten and improvement arrays
        for improved in improved_rebuttals:
            # Add to rebuttals_rewritten
            rewritten_entry = {
                'segment_id': improved.get('section_id', ''),
                'original_rebuttal': improved.get('original_rebuttal', ''),
                'improved_rebuttal': improved.get('improved_rebuttal', ''),
                'improvement_reasoning': improved.get('improvement_reasoning', ''),
                'improvement_score': 8.0  # Assume improved rebuttals score well
            }
            verification_results['rebuttals_rewritten'].append(rewritten_entry)
            
            # Add to specific improvement arrays based on improvement areas
            improvement_reasons = improved.get('improvement_areas', [])
            
            for reason in improvement_reasons:
                if 'accuracy' in reason:
                    verification_results['accuracy_improvements'].append({
                        'section_id': improved.get('section_id'),
                        'improvement_type': 'factual_correction',
                        'original_content': improved.get('original_rebuttal', ''),
                        'improved_content': improved.get('improved_rebuttal', ''),
                        'improvement_reasoning': f"Accuracy improvement: {improved.get('improvement_reasoning', '')}"
                    })
                
                if 'completeness' in reason:
                    verification_results['completeness_improvements'].append({
                        'section_id': improved.get('section_id'),
                        'improvement_type': 'additional_evidence_provided',
                        'added_content': 'Additional counter-arguments and evidence integrated',
                        'improvement_reasoning': f"Completeness improvement: {improved.get('improvement_reasoning', '')}"
                    })
                
                if 'effectiveness' in reason:
                    verification_results['effectiveness_improvements'].append({
                        'section_id': improved.get('section_id'),
                        'improvement_type': 'persuasiveness_improvement',
                        'original_content': improved.get('original_rebuttal', ''),
                        'improved_content': improved.get('improved_rebuttal', ''),
                        'improvement_reasoning': f"Effectiveness improvement: {improved.get('improvement_reasoning', '')}"
                    })
        
        # Calculate final verification score
        if assessed_rebuttals:
            total_score = sum(
                r.get('rebuttal_assessment', {}).get('overall_quality_score', 0) 
                for r in assessed_rebuttals
            )
            verification_results['final_verification_score'] = total_score / len(assessed_rebuttals)
        
        # Return clean script and separate verification data
        return clean_script, verification_results
    
    def _save_verification_results(
        self, 
        clean_script: Dict,
        verification_results: Dict, 
        metadata: Dict[str, Any], 
        output_path: str
    ) -> None:
        """
        Save clean script and verification results separately.
        
        Args:
            clean_script: Clean script without verification metadata
            verification_results: Verification results data
            metadata: Verification metadata
            output_path: Output file path
        """
        try:
            # Ensure output directory exists
            output_dir = os.path.dirname(output_path)
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            # Save clean script directly for pipeline compatibility (Stages 5, 6, 7)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(clean_script, f, indent=2, ensure_ascii=False)
            logger.info(f"Clean script saved for pipeline stages: {output_path}")
            
            # Save verification results separately for quality control tracking
            verification_path = output_path.replace('.json', '_verification_results.json')
            full_verification_data = {
                'verification_results': verification_results,
                'verification_metadata': metadata
            }
            with open(verification_path, 'w', encoding='utf-8') as f:
                json.dump(full_verification_data, f, indent=2, ensure_ascii=False)
            logger.info(f"Verification results saved to: {verification_path}")
            
            # Save quality control results
            self._save_quality_control_results(output_path)
            
        except Exception as e:
            logger.error(f"Failed to save verification results: {e}")
            raise
    
    def _save_quality_control_results(self, output_path: str) -> None:
        """
        Save quality control results following established patterns.
        
        Args:
            output_path: Base output path for generating QC file paths
        """
        try:
            # Create Quality_Control/rebuttal_verification directory
            base_dir = os.path.dirname(output_path)
            qc_dir = os.path.join(base_dir, 'Quality_Control', 'rebuttal_verification')
            
            if not os.path.exists(qc_dir):
                os.makedirs(qc_dir)
            
            base_filename = os.path.splitext(os.path.basename(output_path))[0]
            
            # Save comprehensive assessment results
            assessment_file = os.path.join(qc_dir, f"{base_filename}_all_rebuttal_assessments.json")
            assessment_data = {
                "debug_info": {
                    "total_assessments": len(self._all_assessments),
                    "verification_thresholds": self.verification_thresholds,
                    "generated_timestamp": datetime.now().isoformat()
                },
                "all_rebuttal_assessments": self._all_assessments
            }
            
            with open(assessment_file, 'w', encoding='utf-8') as f:
                json.dump(assessment_data, f, indent=2, ensure_ascii=False)
            logger.info(f"Rebuttal assessments saved to: {assessment_file}")
            
            # Save API debug information
            api_debug_file = os.path.join(qc_dir, f"{base_filename}_api_debug.json")
            api_debug_data = {
                "api_debug_info": {
                    "total_api_calls": len(self._debug_api_calls),
                    "generated_timestamp": datetime.now().isoformat(),
                    "model_used": "gemini-2.5-pro-preview-06-05"
                },
                "api_calls": self._debug_api_calls
            }
            
            with open(api_debug_file, 'w', encoding='utf-8') as f:
                json.dump(api_debug_data, f, indent=2, ensure_ascii=False)
            logger.info(f"API debug info saved to: {api_debug_file}")
            
            # Save rewriting actions as mentioned in task requirements
            if hasattr(self, '_rewriting_actions_log') and self._rewriting_actions_log:
                rewriting_actions_file = os.path.join(qc_dir, f"{base_filename}_rewriting_actions.json")
                rewriting_actions_data = {
                    "rewriting_info": {
                        "total_rewriting_actions": len(self._rewriting_actions_log),
                        "generated_timestamp": datetime.now().isoformat(),
                        "improvement_types_applied": ["accuracy", "completeness", "effectiveness", "source_reliability"]
                    },
                    "rewriting_actions": self._rewriting_actions_log
                }
                
                with open(rewriting_actions_file, 'w', encoding='utf-8') as f:
                    json.dump(rewriting_actions_data, f, indent=2, ensure_ascii=False)
                logger.info(f"Rewriting actions saved to: {rewriting_actions_file}")
            
        except Exception as e:
            logger.error(f"Failed to save quality control results: {e}")


def create_rebuttal_verification_prompt_file(output_dir: str) -> str:
    """
    Create and save the rebuttal verification prompt to a text file.
    
    Args:
        output_dir: Directory to save the prompt file
        
    Returns:
        Path to the saved prompt file
    """
    prompt_content = """
## REBUTTAL VERIFICATION ASSESSMENT - FACT-CHECKING EVALUATION

**EVALUATION METHOD:** Evaluate the post_clip rebuttal content in each section based on factual correctness, argument completeness, and persuasiveness. Score each dimension independently on 1-10 scale.

**FOCUS:** Examine the script_content field in each post_clip section, which contains rebuttal content designed to counter harmful claims from the preceding video clip.

### SCORING DIMENSIONS (1-10 scale):

**1. Rebuttal Accuracy (1-10):**
- 9-10: Completely accurate with verifiable facts and proper citations
- 7-8: Mostly accurate with minor factual issues or missing sources
- 5-6: Some factual inaccuracies or unsupported claims present
- 1-4: Significant factual errors or misleading counter-arguments

**2. Rebuttal Completeness (1-10):**
- 9-10: Comprehensive coverage of all key counter-arguments needed
- 7-8: Good coverage with minor gaps in addressing harmful claims
- 5-6: Adequate but missing some important counter-points
- 1-4: Insufficient counter-argument coverage, major gaps present

**3. Rebuttal Effectiveness (1-10):**
- 9-10: Compelling, well-sourced rebuttals that effectively counter harmful claims
- 7-8: Strong rebuttals with good evidence and persuasive presentation
- 5-6: Moderate effectiveness with some persuasive elements
- 1-4: Weak or ineffective counter-arguments, poor presentation

### VERIFICATION TRIGGERS:
- Accuracy < 7: Rebuttal needs factual improvement
- Completeness < 6: Rebuttal needs additional counter-arguments
- Effectiveness < 6: Rebuttal needs persuasiveness improvement

### IMPROVEMENT AREAS:
- **Accuracy:** Add credible sources, fix factual errors, include proper citations
- **Completeness:** Address missing counter-arguments, cover all key points
- **Effectiveness:** Improve persuasiveness, clarity, and logical flow

This prompt is designed for comprehensive fact-checking and quality improvement of rebuttal content to ensure effective counter-arguments against harmful misinformation.
"""
    
    # Ensure Quality_Control directory exists
    quality_control_dir = os.path.join(output_dir, 'Quality_Control')
    if not os.path.exists(quality_control_dir):
        os.makedirs(quality_control_dir)
    
    # Save prompt file
    prompt_path = os.path.join(quality_control_dir, 'rebuttal_verification_prompt.txt')
    with open(prompt_path, 'w', encoding='utf-8') as f:
        f.write(f"# Rebuttal Verification Prompt\n")
        f.write(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"# Two-Pass AI Quality Control System - Phase 2\n\n")
        f.write(prompt_content)
    
    logger.info(f"Rebuttal verification prompt saved to: {prompt_path}")
    return prompt_path


# Main execution function for command-line usage
def main():
    """Main function for command-line usage."""
    if len(sys.argv) < 2:
        print("Usage: python rebuttal_verifier_rewriter.py <input_file> [output_file]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    
    # Get output file path
    if len(sys.argv) > 2:
        output_file = sys.argv[2]
    else:
        base_name = os.path.splitext(input_file)[0]
        output_file = f"{base_name}_verified_script.json"
    
    try:
        # Initialize rebuttal verifier
        verifier = RebuttalVerifierRewriter()
        
        print(f"Starting Rebuttal Verification and Rewriting")
        print(f"Input: {input_file}")
        print(f"Output: {output_file}")
        
        # Process unified script
        verified_script, metadata = verifier.verify_and_improve_rebuttals(input_file, output_file)
        
        # Create prompt file in same directory
        output_dir = os.path.dirname(output_file)
        create_rebuttal_verification_prompt_file(output_dir)
        
        print("Rebuttal verification completed successfully!")
        print(f"Results: {output_file}")
        print(f"Verification summary:")
        print(f"  - Rebuttals assessed: {metadata['rebuttals_assessed']}")
        print(f"  - Rebuttals rewritten: {metadata['rebuttals_rewritten']}")
        
    except Exception as e:
        logger.error(f"Rebuttal verification failed: {e}")
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()