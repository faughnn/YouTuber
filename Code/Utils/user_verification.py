"""
User Verification Module

Provides interactive verification functionality for host/guest name extraction.
This module handles the user prompt system when `prompt_for_verification` is enabled.
Enhanced with preview mode and rule learning capabilities.
"""

import sys
import json
import os
from typing import Dict, Tuple

# Handle imports properly for both direct execution and module imports
try:
    from .file_organizer import FileOrganizer
    from .config_manager import get_config
except ImportError:
    # This allows the script to be run directly for testing
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
    from Utils.file_organizer import FileOrganizer
    from Utils.config_manager import get_config

class UserVerification:
    """Handles user interaction for verifying and correcting extracted names."""
    
    @staticmethod
    def prompt_for_verification(extracted_names: Dict[str, str], metadata: Dict) -> Dict[str, str]:
        """
        Prompts the user to verify or correct the extracted host and guest names.
        Enhanced with preview mode and rule learning capabilities.
        
        Args:
            extracted_names: Dictionary with 'host' and 'guest' keys
            metadata: Original video metadata (title, uploader, etc.)
            
        Returns:
            Dictionary with verified 'host' and 'guest' names
        """
        print("\n" + "="*60)
        print("🎯 NAME EXTRACTION VERIFICATION")
        print("="*60)
        print(f"📺 Video Title: {metadata.get('title', 'Unknown')}")
        print(f"📢 Uploader: {metadata.get('uploader', 'Unknown')}")
        print("-"*60)
        print("🤖 Automatically Extracted Names:")
        print(f"   Host: {extracted_names['host']}")
        print(f"   Guest: {extracted_names['guest']}")
        
        # Preview Mode: Show proposed folder structure
        UserVerification._show_preview(extracted_names, metadata)
        
        print("-"*60)
        
        # Verify host name
        verified_host = UserVerification._verify_single_name(
            "Host/Show", 
            extracted_names['host']
        )
        
        # Verify guest name
        verified_guest = UserVerification._verify_single_name(
            "Guest", 
            extracted_names['guest']
        )
        
        # Final confirmation
        print("\n" + "="*60)
        print("📋 FINAL VERIFICATION")
        print("="*60)
        print(f"✅ Host: {verified_host}")
        print(f"✅ Guest: {verified_guest}")
        
        # Show final folder structure
        final_names = {'host': verified_host, 'guest': verified_guest}
        UserVerification._show_preview(final_names, metadata, final=True)
        
        confirm = input("\n🔍 Are these names correct? (y/n): ").strip().lower()
        if confirm not in ['y', 'yes']:
            print("🔄 Let's try again...")
            return UserVerification.prompt_for_verification(
                {'host': verified_host, 'guest': verified_guest}, 
                metadata
            )
        
        # Rule Learning: Offer to save corrections as new rules
        if (verified_host != extracted_names['host'] or verified_guest != extracted_names['guest']):
            UserVerification._offer_rule_learning(extracted_names, final_names, metadata)
        
        print("✅ Names verified! Proceeding with download...")
        return final_names
    
    @staticmethod
    def _verify_single_name(name_type: str, current_name: str) -> str:
        """
        Verify or correct a single name (host or guest).
        
        Args:
            name_type: "Host/Show" or "Guest"
            current_name: Current extracted name
            
        Returns:
            Verified name
        """
        while True:
            print(f"\n🏷️  {name_type} Name Verification:")
            print(f"   Current: {current_name}")
            
            action = input(f"   (k)eep, (e)dit, or (c)lear {name_type.lower()} name? [k/e/c]: ").strip().lower()
            
            if action in ['k', 'keep', '']:
                return current_name
            elif action in ['e', 'edit']:
                new_name = input(f"   Enter new {name_type.lower()} name: ").strip()
                if new_name:
                    return new_name
                else:
                    print("   ❌ Name cannot be empty. Please try again.")
            elif action in ['c', 'clear']:
                if name_type == "Guest":
                    return "No Guest"
                else:
                    print("   ❌ Host name cannot be cleared. Please try again.")
            else:
                print("   ❌ Invalid option. Please choose 'k', 'e', or 'c'.")
    
    @staticmethod
    def _show_preview(names: Dict[str, str], metadata: Dict, final: bool = False) -> None:
        """
        Show preview of the folder structure that will be created.
        
        Args:
            names: Dictionary with 'host' and 'guest' keys
            metadata: Video metadata
            final: Whether this is the final preview
        """
        try:
            # Use FileOrganizer to get the actual paths that would be created
            # We need to create a temporary FileOrganizer with default config
            temp_organizer = FileOrganizer({'episode_base': 'Content'})
            
            preview_paths = temp_organizer.get_episode_paths(
                metadata.get('title', 'Unknown Title'),
                names['host'],
                names['guest']
            )
            
            prefix = "🎯 FINAL" if final else "👀 PREVIEW"
            print(f"\n{prefix} - Folder Structure:")
            print(f"   📁 {preview_paths['episode_folder']}")
            print(f"      ├── Input/")
            print(f"      ├── Processing/")
            print(f"      └── Output/")
            
        except Exception as e:
            print(f"\n👀 PREVIEW - Folder Structure: (Error generating preview: {e})")
            print(f"   📁 Content/{names['host']}/...")
    
    @staticmethod
    def _offer_rule_learning(original_names: Dict[str, str], corrected_names: Dict[str, str], metadata: Dict) -> None:
        """
        Offer to save user corrections as new uploader-specific rules.
        
        Args:
            original_names: Originally extracted names
            corrected_names: User-corrected names
            metadata: Video metadata
        """
        uploader = metadata.get('uploader', '')
        title = metadata.get('title', '')
        
        if not uploader:
            return
        
        print(f"\n🤖 RULE LEARNING")
        print(f"You corrected the extraction for '{uploader}'")
        print(f"Original: Host='{original_names['host']}', Guest='{original_names['guest']}'")
        print(f"Corrected: Host='{corrected_names['host']}', Guest='{corrected_names['guest']}'")
        
        # Analyze the correction pattern
        suggested_rule = UserVerification._analyze_correction_pattern(title, corrected_names['guest'])
        
        if suggested_rule:
            print(f"\n💡 Suggested rule for '{uploader}':")
            print(f"   Strategy: {suggested_rule['strategy']}")
            print(f"   Parameter: '{suggested_rule['parameter']}'")
            
            save_rule = input(f"\n💾 Save this rule for future videos from '{uploader}'? (y/n): ").strip().lower()
            
            if save_rule in ['y', 'yes']:
                UserVerification._save_new_rule(uploader, suggested_rule)
                print("✅ Rule saved successfully!")
            else:
                print("⏭️ Rule not saved.")
        else:
            print("\n❓ Could not determine a clear pattern from your correction.")
            print("   Consider manually adding a rule to the configuration file.")
    
    @staticmethod
    def _analyze_correction_pattern(title: str, corrected_guest: str) -> Dict[str, str]:
        """
        Analyze user correction to suggest a new rule pattern.
        
        Args:
            title: Video title
            corrected_guest: User-corrected guest name
            
        Returns:
            Suggested rule or None if no pattern found
        """
        if corrected_guest == "No Guest":
            return {'strategy': 'none', 'parameter': ''}
        
        # Look for delimiter patterns
        common_delimiters = [' - ', ' | ', ': ']
        for delimiter in common_delimiters:
            if delimiter in title:
                parts = title.split(delimiter)
                for part in parts:
                    if corrected_guest.lower() in part.lower():
                        return {'strategy': 'split', 'parameter': delimiter}
        
        # Look for keyword patterns
        common_keywords = [' with ', ' feat. ', ' ft. ', ' featuring ', ' guest: ']
        for keyword in common_keywords:
            if keyword in title.lower():
                # Check if guest appears after this keyword
                keyword_pos = title.lower().find(keyword)
                if keyword_pos != -1:
                    after_keyword = title[keyword_pos + len(keyword):].strip()
                    if corrected_guest.lower() in after_keyword.lower():
                        return {'strategy': 'keyword', 'parameter': keyword}
        
        return None
    
    @staticmethod
    def _save_new_rule(uploader: str, rule: Dict[str, str]) -> None:
        """
        Save a new uploader-specific rule to the configuration file.
        
        Args:
            uploader: Channel/uploader name
            rule: Rule definition
        """
        try:
            config_path = os.path.abspath('Code/Config/name_extractor_rules.json')
            
            # Load current config
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # Add new rule
            if 'uploader_rules' not in config:
                config['uploader_rules'] = {}
            
            config['uploader_rules'][uploader] = {
                'strategy': rule['strategy'],
                'parameter': rule['parameter']
            }
            
            # If split strategy, add default 'select' parameter
            if rule['strategy'] == 'split':
                config['uploader_rules'][uploader]['select'] = 'last'
            
            # Save updated config
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"❌ Error saving rule: {e}")

# Example usage
if __name__ == '__main__':
    print("Running UserVerification example...")
    
    # Mock metadata and extracted names
    test_metadata = {
        'title': 'Joe Rogan Experience #2000 - Elon Musk',
        'uploader': 'PowerfulJRE'
    }
    
    test_extracted = {
        'host': 'PowerfulJRE',
        'guest': 'Elon Musk'
    }
    
    # Test verification
    verified = UserVerification.prompt_for_verification(test_extracted, test_metadata)
    print(f"\nFinal result: Host='{verified['host']}', Guest='{verified['guest']}'")
