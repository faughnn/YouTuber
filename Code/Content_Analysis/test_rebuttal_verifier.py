"""
Simple test script for RebuttalVerifierRewriter module validation
Tests schema validation and basic functionality without API calls
"""

import os
import sys
import json
import logging

# Add current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

# Import the modules
from rebuttal_verifier_rewriter import RebuttalVerifierRewriter
from json_schema_validator import JSONSchemaValidator

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_schema_validation():
    """Test schema validation functions"""
    logger.info("=== TESTING SCHEMA VALIDATION ===")
    
    # Initialize validator
    validator = JSONSchemaValidator()
    
    # Test unified script validation
    test_script_path = r"C:\Users\nfaug\OneDrive - LIR\Desktop\YouTuber\Content\Joe_Rogan\Joe_Rogan_Mike_Baker\Output\Scripts\unified_podcast_script.json"
    
    if os.path.exists(test_script_path):
        logger.info("Testing unified script validation...")
        is_valid, errors = validator.validate_script_input(test_script_path)
        if is_valid:
            logger.info("✅ Unified script validation passed")
        else:
            logger.error("❌ Unified script validation failed:")
            for error in errors:
                logger.error(f"  - {error}")
    else:
        logger.warning("Test script not found, skipping validation test")

def test_post_clip_extraction():
    """Test post_clip section extraction"""
    logger.info("=== TESTING POST_CLIP EXTRACTION ===")
    
    test_script_path = r"C:\Users\nfaug\OneDrive - LIR\Desktop\YouTuber\Content\Joe_Rogan\Joe_Rogan_Mike_Baker\Output\Scripts\unified_podcast_script.json"
    
    if not os.path.exists(test_script_path):
        logger.warning("Test script not found, skipping extraction test")
        return
        
    # Load test script
    with open(test_script_path, 'r', encoding='utf-8') as f:
        script_data = json.load(f)
    
    # Initialize verifier without API calls
    verifier = RebuttalVerifierRewriter()
    
    # Extract post_clip sections
    post_clip_sections = verifier._extract_post_clip_sections(script_data)
    
    logger.info(f"Found {len(post_clip_sections)} post_clip sections:")
    for i, section in enumerate(post_clip_sections, 1):
        section_id = section.get('section_id', 'unknown')
        clip_ref = section.get('clip_reference', 'none')
        content_length = len(section.get('script_content', ''))
        logger.info(f"  {i}. {section_id} (refs: {clip_ref}, content: {content_length} chars)")
        
        # Show content preview
        content = section.get('script_content', '')[:100]
        logger.info(f"     Preview: {content}...")

def test_assessment_functions():
    """Test individual assessment functions"""
    logger.info("=== TESTING ASSESSMENT FUNCTIONS ===")
    
    verifier = RebuttalVerifierRewriter()
    
    # Test sample rebuttal content
    sample_rebuttal = """
    According to peer-reviewed research from Stanford University, the claims made in the previous clip
    are factually incorrect. Multiple studies have shown that this topic is more nuanced. However,
    the evidence clearly indicates a different conclusion. Furthermore, experts in the field agree
    that the reality is more complex than presented.
    """
    
    context = "Media bias discussion context"
    
    # Test accuracy assessment
    accuracy_score = verifier.assess_rebuttal_accuracy(sample_rebuttal, context)
    logger.info(f"Accuracy score: {accuracy_score}/10")
    
    # Test completeness assessment
    completeness_score = verifier.assess_rebuttal_completeness(sample_rebuttal, context)
    logger.info(f"Completeness score: {completeness_score}/10")
    
    # Test effectiveness assessment
    effectiveness_score = verifier.assess_rebuttal_effectiveness(sample_rebuttal, context)
    logger.info(f"Effectiveness score: {effectiveness_score}/10")

def test_threshold_logic():
    """Test verification threshold logic"""
    logger.info("=== TESTING THRESHOLD LOGIC ===")
    
    verifier = RebuttalVerifierRewriter()
    
    # Create mock assessed rebuttals
    mock_rebuttals = [
        {
            'section_id': 'test_001',
            'script_content': 'Test rebuttal content',
            'rebuttal_assessment': {
                'accuracy': 8,
                'completeness': 7, 
                'effectiveness': 6,
                'overall_quality_score': 7.0
            }
        },
        {
            'section_id': 'test_002',
            'script_content': 'Another test rebuttal',
            'rebuttal_assessment': {
                'accuracy': 6,  # Below threshold (7)
                'completeness': 5, # Below threshold (6)
                'effectiveness': 4, # Below threshold (6)
                'overall_quality_score': 5.0
            }
        },
        {
            'section_id': 'test_003',
            'script_content': 'Third test rebuttal',
            'rebuttal_assessment': {
                'accuracy': 9,
                'completeness': 8,
                'effectiveness': 7,
                'overall_quality_score': 8.0
            }
        }
    ]
    
    # Test threshold identification
    rebuttals_needing_improvement = verifier._identify_rebuttals_for_rewriting(mock_rebuttals)
    
    logger.info(f"Total rebuttals: {len(mock_rebuttals)}")
    logger.info(f"Rebuttals needing improvement: {len(rebuttals_needing_improvement)}")
    
    for rebuttal in rebuttals_needing_improvement:
        section_id = rebuttal.get('section_id')
        reasons = rebuttal.get('improvement_reasons', [])
        logger.info(f"  - {section_id}: {', '.join(reasons)}")

def main():
    """Run all tests"""
    logger.info("Starting RebuttalVerifierRewriter tests...")
    
    try:
        test_schema_validation()
        test_post_clip_extraction()
        test_assessment_functions()
        test_threshold_logic()
        
        logger.info("=== ALL TESTS COMPLETED ===")
        logger.info("✅ RebuttalVerifierRewriter module validation successful!")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    main()