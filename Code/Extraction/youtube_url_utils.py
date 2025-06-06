#!/usr/bin/env python3
"""
YouTube URL Utilities Module

This module provides comprehensive YouTube URL validation, sanitization, and video ID extraction
functionality for use across all extraction modules.

Created: June 5, 2025
Author: YouTube Content Processing Pipeline
"""

import re
import urllib.parse
from typing import Dict, Optional, List, Any


class YouTubeUrlUtils:
    """Utility class for YouTube URL processing and validation."""
    
    # Supported YouTube URL patterns
    URL_PATTERNS = [
        r'https?://(?:www\.)?youtube\.com/watch\?v=([\w-]+)',        # Standard
        r'https?://youtu\.be/([\w-]+)',                             # Short
        r'https?://(?:www\.)?youtube\.com/embed/([\w-]+)',          # Embed
        r'https?://(?:www\.)?youtube\.com/v/([\w-]+)',              # /v/ format
        r'https?://(?:m\.)?youtube\.com/watch\?v=([\w-]+)',         # Mobile
        r'https?://(?:www\.)?youtube\.com/shorts/([\w-]+)',         # Shorts
        r'^([\w-]{11})$'                                            # Direct video ID
    ]
    
    # Valid YouTube domains
    VALID_DOMAINS = [
        'youtube.com',
        'www.youtube.com', 
        'm.youtube.com',
        'youtu.be'
    ]
    
    # Tracking parameters to remove during sanitization
    TRACKING_PARAMS = {
        'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content',
        'fbclid', 'gclid', 'dclid', 'msclkid', '_ga', 'mc_cid', 'mc_eid'
    }
    
    # Safe parameters to preserve
    SAFE_PARAMS = {'t', 'feature', 'si'}
    
    @classmethod
    def validate_youtube_url(cls, url: str) -> bool:
        """
        Validate if the input is a valid YouTube URL or video ID.
        
        Args:
            url: The URL or video ID to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        if not url or not isinstance(url, str):
            return False
            
        url = url.strip()
        if not url:
            return False
            
        # Check against all supported patterns
        for pattern in cls.URL_PATTERNS:
            if re.match(pattern, url):
                return True
                
        return False
    
    @classmethod
    def extract_video_id(cls, url: str) -> Optional[str]:
        """
        Extract video ID from various YouTube URL formats.
        
        Args:
            url: YouTube URL or video ID
            
        Returns:
            str: 11-character video ID if found, None otherwise
        """
        if not url or not isinstance(url, str):
            return None
            
        url = url.strip()
        if not url:
            return None
            
        # Try each pattern to extract video ID
        for pattern in cls.URL_PATTERNS:
            match = re.match(pattern, url)
            if match:
                video_id = match.group(1)
                if cls.is_valid_video_id(video_id):
                    return video_id
                    
        return None
    
    @classmethod
    def is_valid_video_id(cls, video_id: str) -> bool:
        """
        Validate YouTube video ID format.
        
        Args:
            video_id: The video ID to validate
            
        Returns:
            bool: True if valid 11-character video ID
        """
        if not video_id or not isinstance(video_id, str):
            return False
            
        # Must be exactly 11 characters
        if len(video_id) != 11:
            return False
            
        # Must contain only valid characters (alphanumeric, hyphens, underscores)
        if not re.match(r'^[\w-]+$', video_id):
            return False
            
        return True
    
    @classmethod
    def is_playlist_url(cls, url: str) -> bool:
        """
        Check if the URL is a playlist URL.
        
        Args:
            url: URL to check
            
        Returns:
            bool: True if playlist URL
        """
        if not url or not isinstance(url, str):
            return False
            
        return 'playlist' in url.lower() or 'list=' in url.lower()
    
    @classmethod
    def sanitize_youtube_url(cls, url: str) -> str:
        """
        Sanitize YouTube URL by removing tracking parameters and normalizing format.
        
        Args:
            url: URL to sanitize
            
        Returns:
            str: Sanitized URL
        """
        if not url or not isinstance(url, str):
            return url
            
        # Extract video ID first
        video_id = cls.extract_video_id(url)
        if not video_id:
            return url
            
        # Parse the URL to handle parameters
        try:
            parsed = urllib.parse.urlparse(url)
            query_params = urllib.parse.parse_qs(parsed.query)
            
            # Build clean parameters (only safe ones)
            clean_params = {}
            for param, values in query_params.items():
                if param.lower() in cls.SAFE_PARAMS and values:
                    clean_params[param] = values[0]
            
            # Reconstruct clean URL
            if clean_params:
                query_string = urllib.parse.urlencode(clean_params)
                clean_url = f"https://www.youtube.com/watch?v={video_id}&{query_string}"
            else:
                clean_url = f"https://www.youtube.com/watch?v={video_id}"
                
            return clean_url
            
        except Exception:
            # Fallback to simple clean URL
            return f"https://www.youtube.com/watch?v={video_id}"
    
    @classmethod
    def is_safe_youtube_url(cls, url: str) -> bool:
        """
        Check if URL is safe (valid YouTube domain, no malicious patterns).
        
        Args:
            url: URL to check
            
        Returns:
            bool: True if safe
        """
        if not url or not isinstance(url, str):
            return False
            
        # Check for obvious malicious patterns
        dangerous_patterns = [
            r'javascript:',
            r'data:',
            r'<script',
            r'\.\./',
            r'%2e%2e%2f',  # URL encoded ../
        ]
        
        url_lower = url.lower()
        for pattern in dangerous_patterns:
            if re.search(pattern, url_lower):
                return False
        
        # Validate domain if it's a full URL
        if url.startswith(('http://', 'https://')):
            return cls.is_valid_youtube_domain(url)
            
        # For video IDs, just validate the format
        return cls.is_valid_video_id(url)
    
    @classmethod
    def is_valid_youtube_domain(cls, url: str) -> bool:
        """
        Validate that the URL uses a legitimate YouTube domain.
        
        Args:
            url: URL to check
            
        Returns:
            bool: True if valid YouTube domain
        """
        if not url or not isinstance(url, str):
            return False
            
        try:
            parsed = urllib.parse.urlparse(url)
            domain = parsed.netloc.lower()
            
            # Remove port if present
            if ':' in domain:
                domain = domain.split(':')[0]
                
            return domain in cls.VALID_DOMAINS
            
        except Exception:
            return False
    
    @classmethod
    def normalize_to_standard_url(cls, url_or_id: str) -> Optional[str]:
        """
        Convert any YouTube URL format or video ID to standard watch URL.
        
        Args:
            url_or_id: YouTube URL or video ID
            
        Returns:
            str: Standard YouTube watch URL, or None if invalid
        """
        video_id = cls.extract_video_id(url_or_id)
        if not video_id:
            return None
            
        return f"https://www.youtube.com/watch?v={video_id}"
    
    @classmethod
    def extract_timestamp(cls, url: str) -> Optional[str]:
        """
        Extract timestamp parameter from YouTube URL.
        
        Args:
            url: YouTube URL
            
        Returns:
            str: Timestamp value (e.g., "30s") or None
        """
        if not url or not isinstance(url, str):
            return None
            
        try:
            parsed = urllib.parse.urlparse(url)
            query_params = urllib.parse.parse_qs(parsed.query)
            
            if 't' in query_params and query_params['t']:
                return query_params['t'][0]
                
        except Exception:
            pass
            
        return None
    
    @classmethod
    def validate_input(cls, input_str: str) -> Dict[str, Any]:
        """
        Comprehensive input validation for YouTube URLs and video IDs.
        
        Args:
            input_str: Input to validate
            
        Returns:
            dict: Validation result with detailed information
        """
        result = {
            'valid': False,
            'type': 'unknown',
            'video_id': None,
            'sanitized_url': None,
            'is_playlist': False,
            'has_timestamp': False,
            'timestamp': None,
            'warnings': [],
            'errors': []
        }
        
        if not input_str or not isinstance(input_str, str):
            result['errors'].append("Input is empty or not a string")
            return result
            
        input_str = input_str.strip()
        if not input_str:
            result['errors'].append("Input is empty after trimming whitespace")
            return result
        
        # Check if it's a YouTube URL/ID
        if not cls.validate_youtube_url(input_str):
            result['errors'].append("Not a valid YouTube URL or video ID")
            return result
        
        # Check safety
        if not cls.is_safe_youtube_url(input_str):
            result['errors'].append("URL contains potentially malicious content")
            return result
        
        # Extract video ID
        video_id = cls.extract_video_id(input_str)
        if not video_id:
            result['errors'].append("Could not extract valid video ID")
            return result
        
        # If we get here, it's valid
        result['valid'] = True
        result['type'] = 'youtube_url'
        result['video_id'] = video_id
        result['sanitized_url'] = cls.sanitize_youtube_url(input_str)
        result['is_playlist'] = cls.is_playlist_url(input_str)
        
        # Check for timestamp
        timestamp = cls.extract_timestamp(input_str)
        if timestamp:
            result['has_timestamp'] = True
            result['timestamp'] = timestamp
        
        # Add warnings for playlist URLs
        if result['is_playlist']:
            result['warnings'].append("Playlist URL detected - will process individual video only")
        
        return result


# Convenience functions for backward compatibility and ease of use
def validate_youtube_url(url: str) -> bool:
    """Validate YouTube URL - convenience function."""
    return YouTubeUrlUtils.validate_youtube_url(url)


def extract_video_id(url: str) -> Optional[str]:
    """Extract video ID - convenience function."""
    return YouTubeUrlUtils.extract_video_id(url)


def sanitize_youtube_url(url: str) -> str:
    """Sanitize YouTube URL - convenience function."""
    return YouTubeUrlUtils.sanitize_youtube_url(url)


def is_valid_video_id(video_id: str) -> bool:
    """Validate video ID - convenience function."""
    return YouTubeUrlUtils.is_valid_video_id(video_id)


def normalize_youtube_input(url_or_id: str) -> Optional[str]:
    """Normalize YouTube input to standard URL - convenience function."""
    return YouTubeUrlUtils.normalize_to_standard_url(url_or_id)


if __name__ == "__main__":
    # Test the utility functions
    test_urls = [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://youtu.be/dQw4w9WgXcQ",
        "dQw4w9WgXcQ",
        "https://youtube.com/watch?v=dQw4w9WgXcQ&t=30s",
        "https://youtube.com/watch?v=dQw4w9WgXcQ&list=PLtest&index=1",
        "invalid_url"
    ]
    
    print("Testing YouTube URL Utilities:")
    print("=" * 50)
    
    for url in test_urls:
        print(f"\nTesting: {url}")
        result = YouTubeUrlUtils.validate_input(url)
        print(f"Valid: {result['valid']}")
        if result['valid']:
            print(f"Video ID: {result['video_id']}")
            print(f"Sanitized: {result['sanitized_url']}")
            print(f"Is Playlist: {result['is_playlist']}")
            if result['warnings']:
                print(f"Warnings: {result['warnings']}")
        else:
            print(f"Errors: {result['errors']}")
