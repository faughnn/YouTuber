"""
Logger Factory - Central factory for creating enhanced loggers
=============================================================

Provides a centralized way to create and configure all types of enhanced loggers
for the YouTube processing pipeline. Ensures consistent logger instances and
configuration across the application.

Features:
- Centralized logger creation
- Consistent configuration
- Easy access to all logger types
- Optional custom configuration support

Created: June 26, 2025
Based on: Enhanced Logging System specification
"""

from .pipeline_logger import PipelineLogger
from .progress_logger import ProgressLogger
from .menu_logger import MenuLogger
from .test_logger import TestLogger

class LoggerFactory:
    """
    Factory class for creating enhanced loggers.
    
    Provides static methods to create properly configured logger instances
    for different use cases in the YouTube processing pipeline.
    """
    
    _pipeline_loggers = {}
    _progress_logger = None
    _menu_logger = None
    _test_logger = None
    
    @staticmethod
    def get_pipeline_logger(name="Pipeline"):
        """
        Get or create a pipeline logger instance.
        
        Args:
            name (str): Name for the pipeline logger (default: "Pipeline")
            
        Returns:
            PipelineLogger: Configured pipeline logger instance
        """
        if name not in LoggerFactory._pipeline_loggers:
            LoggerFactory._pipeline_loggers[name] = PipelineLogger(name)
        return LoggerFactory._pipeline_loggers[name]
    
    @staticmethod
    def get_progress_logger():
        """
        Get or create a progress logger instance.
        
        Returns:
            ProgressLogger: Configured progress logger instance
        """
        if LoggerFactory._progress_logger is None:
            LoggerFactory._progress_logger = ProgressLogger()
        return LoggerFactory._progress_logger
    
    @staticmethod
    def get_menu_logger():
        """
        Get or create a menu logger instance.
        
        Returns:
            MenuLogger: Configured menu logger instance
        """
        if LoggerFactory._menu_logger is None:
            LoggerFactory._menu_logger = MenuLogger()
        return LoggerFactory._menu_logger
    
    @staticmethod
    def get_test_logger():
        """
        Get or create a test logger instance.
        
        Returns:
            TestLogger: Configured test logger instance
        """
        if LoggerFactory._test_logger is None:
            LoggerFactory._test_logger = TestLogger()
        return LoggerFactory._test_logger
    
    @staticmethod
    def reset_loggers():
        """
        Reset all logger instances.
        
        Useful for testing or when you need fresh logger instances.
        """
        LoggerFactory._pipeline_loggers.clear()
        LoggerFactory._progress_logger = None
        LoggerFactory._menu_logger = None
        LoggerFactory._test_logger = None
    
    @staticmethod
    def create_custom_pipeline_logger(name, config=None):
        """
        Create a custom pipeline logger with specific configuration.
        
        Args:
            name (str): Name for the pipeline logger
            config (dict, optional): Custom configuration dictionary
            
        Returns:
            PipelineLogger: Configured pipeline logger instance
        """
        logger = PipelineLogger(name)
        
        # Apply custom configuration if provided
        if config:
            # Future: Add configuration options like colors, formatting, etc.
            pass
            
        return logger

# Convenience functions for easy import and use
def get_pipeline_logger(name="Pipeline"):
    """
    Convenience function to get a pipeline logger.
    
    Args:
        name (str): Name for the pipeline logger
        
    Returns:
        PipelineLogger: Configured pipeline logger instance
    """
    return LoggerFactory.get_pipeline_logger(name)

def get_progress_logger():
    """
    Convenience function to get a progress logger.
    
    Returns:
        ProgressLogger: Configured progress logger instance
    """
    return LoggerFactory.get_progress_logger()

def get_menu_logger():
    """
    Convenience function to get a menu logger.
    
    Returns:
        MenuLogger: Configured menu logger instance
    """
    return LoggerFactory.get_menu_logger()

def get_test_logger():
    """
    Convenience function to get a test logger.
    
    Returns:
        TestLogger: Configured test logger instance
    """
    return LoggerFactory.get_test_logger()

# Quick access to most commonly used loggers
pipeline_logger = lambda name="Pipeline": get_pipeline_logger(name)
progress_logger = get_progress_logger
menu_logger = get_menu_logger
test_logger = get_test_logger
