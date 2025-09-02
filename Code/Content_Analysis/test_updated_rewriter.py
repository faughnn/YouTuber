"""
Test the updated rewriting prompt with Alternative Media Literacy voice
"""

import os
import sys
import json

# Add current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from rebuttal_verifier_rewriter import RebuttalVerifierRewriter

def test_updated_rewriting_prompt():
    """Test that the updated rewriting prompt generates correctly"""
    
    # Create verifier
    verifier = RebuttalVerifierRewriter()
    
    # Create mock rebuttal data
    mock_rebuttals = [
        {
            'section_id': 'post_clip_001',
            'script_content': 'According to research, this claim is factually incorrect. Multiple studies indicate different conclusions.',
            'rebuttal_assessment': {
                'accuracy': 6,  # Below threshold (7)
                'completeness': 5,  # Below threshold (6)
                'effectiveness': 4,  # Below threshold (6)
                'overall_quality_score': 5.0
            },
            'improvement_reasons': ['accuracy: 6 < 7', 'completeness: 5 < 6', 'effectiveness: 4 < 6'],
            'clip_reference': 'Harmful_Segment_02'
        }
    ]
    
    # Generate rewriting prompt
    prompt = verifier._create_rebuttal_rewriting_prompt(mock_rebuttals)
    
    print("=== UPDATED REWRITING PROMPT TEST ===")
    print(f"Prompt length: {len(prompt)} characters")
    print("\n=== PROMPT CONTENT PREVIEW ===")
    print(prompt[:1000] + "..." if len(prompt) > 1000 else prompt)
    
    # Check for key elements
    key_elements = [
        "Alternative Media Literacy",
        "Jon Stewart",
        "sarcastic", 
        "TTS",
        "conversational",
        "receipts",
        "entertaining",
        "Complete garbage"
    ]
    
    print("\n=== KEY ELEMENTS CHECK ===")
    for element in key_elements:
        present = element in prompt
        print(f"✅ {element}: {'Found' if present else '❌ Missing'}")
    
    return prompt

if __name__ == "__main__":
    test_updated_rewriting_prompt()