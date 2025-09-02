"""
Name Extractor Module

This module contains the core logic for extracting Host and Guest names
from YouTube video metadata (title and uploader). It uses a hierarchical
strategy defined in the project plan.
"""

import re
from .config_manager import get_setting, get_uploader_rule, get_host_mapping

class NameExtractor:
    def __init__(self, title, uploader):
        self.original_title = title
        self.uploader = uploader
        self.host = self._sanitize(uploader)
        self.guest = "No Guest"

    def extract(self):
        """
        Executes the name extraction process.
        Enhanced with uploader-as-host principle and rule tracking.
        
        Returns:
            dict: A dictionary containing the 'host', 'guest', and 'rule_used'.
        """
        # Check for host mapping first, then use uploader as fallback
        mapped_host = get_host_mapping(self.uploader)
        self.host = mapped_host if mapped_host else self.uploader
        
        cleaned_title = self._sanitize_title(self.original_title)
        rule_used = "none"
        
        # Tier 1: Uploader-Specific Rules
        rule = get_uploader_rule(self.uploader)
        if rule:
            self._apply_specific_rule(cleaned_title, rule)
            rule_used = f"uploader_rule_{rule.get('strategy', 'unknown')}"
        else:
            # Tier 2 & 3: Generic Extraction
            if self._apply_generic_rules(cleaned_title):
                rule_used = "generic_rule"
            else:
                rule_used = "fallback"
            
        return {
            "host": self.host,
            "guest": self._sanitize(self.guest),
            "rule_used": rule_used
        }

    def _apply_specific_rule(self, title, rule):
        strategy = rule.get('strategy')
        param = rule.get('parameter')
        
        if strategy == 'split' and param:
            parts = title.split(param)
            if len(parts) > 1:
                # As per plan, 'select: last' is the default for split
                self.guest = parts[-1]
        elif strategy == 'keyword' and param:
            if param in title:
                self.guest = title.split(param)[-1]
        elif strategy == 'none':
            self.guest = "No Guest"

    def _apply_generic_rules(self, title):
        """
        Apply generic rules for guest extraction.
        Enhanced to return success/failure for rule tracking.
        
        Returns:
            bool: True if a rule successfully extracted a guest, False otherwise
        """
        # Tier 2: Generic Keyword Extraction
        keywords = [' with ', ' feat. ', ' ft. ', ' guest: ', ' featuring ', ' & ', ' and ']
        for keyword in keywords:
            if keyword in title:
                self.guest = title.split(keyword)[-1]
                return True  # Stop after finding the first keyword match

        # Tier 3: Generic Delimiter Extraction
        delimiters = [' | ', ': ', ' - ']
        for delimiter in delimiters:
            if delimiter in title:
                self.guest = title.split(delimiter)[-1]
                return True  # Stop after finding the first delimiter match
        
        # No rule applied successfully
        return False

    def _sanitize_title(self, title):
        """Removes common YouTube clutter from titles."""
        # Remove patterns like (Official Video), [4K], etc.
        title = re.sub(r'\[.*?\]', '', title)
        title = re.sub(r'\(.*?\)', '', title)
        # Remove episode numbers
        title = re.sub(r'#\d+', '', title)
        title = re.sub(r'Ep\.\s*\d+', '', title)
        return title.strip()

    def _sanitize(self, name):
        """A basic sanitizer for file/folder names."""
        if not name:
            return ""
        # Replace problematic characters with an underscore
        return re.sub(r'[\\/*?:"<>|]', '_', name).strip()

# Example Usage
if __name__ == '__main__':
    print("Running NameExtractor examples...")

    # Example 1: Joe Rogan (Specific Split Rule)
    extractor1 = NameExtractor("Joe Rogan Experience #123 - Guest Name", "PowerfulJRE")
    result1 = extractor1.extract()
    print(f"Uploader: PowerfulJRE -> Host: {result1['host']}, Guest: {result1['guest']}")

    # Example 2: Bret Weinstein (Specific Keyword Rule)
    extractor2 = NameExtractor("DarkHorse Podcast with Another Guest", "Bret Weinstein")
    result2 = extractor2.extract()
    print(f"Uploader: Bret Weinstein -> Host: {result2['host']}, Guest: {result2['guest']}")

    # Example 3: Generic Keyword
    extractor3 = NameExtractor("Some Show feat. A Generic Guest", "SomeRandomChannel")
    result3 = extractor3.extract()
    print(f"Uploader: SomeRandomChannel (Keyword) -> Host: {result3['host']}, Guest: {result3['guest']}")

    # Example 4: Generic Delimiter
    extractor4 = NameExtractor("Another Show | Topic Or Guest", "AnotherChannel")
    result4 = extractor4.extract()
    print(f"Uploader: AnotherChannel (Delimiter) -> Host: {result4['host']}, Guest: {result4['guest']}")

    # Example 5: No Guest Found
    extractor5 = NameExtractor("Just a regular video title", "MyChannel")
    result5 = extractor5.extract()
    print(f"Uploader: MyChannel (Fallback) -> Host: {result5['host']}, Guest: {result5['guest']}")