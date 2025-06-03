"""
Error Handling and Recovery Utilities for Master Processor

Provides error handling, retry mechanisms, and recovery functionality.
"""

import time
import logging
import traceback
from typing import Optional, Callable, Any, Dict, List
from dataclasses import dataclass
from enum import Enum


class ErrorCategory(Enum):
    """Categories of errors that can occur during processing."""
    NETWORK_ERROR = "network_error"
    PROCESSING_ERROR = "processing_error"
    API_ERROR = "api_error"
    SYSTEM_ERROR = "system_error"
    VALIDATION_ERROR = "validation_error"


@dataclass
class ErrorInfo:
    """Information about an error that occurred."""
    category: ErrorCategory
    message: str
    stage: str
    timestamp: float
    traceback_info: Optional[str] = None
    suggestion: Optional[str] = None
    retry_count: int = 0


class ErrorHandler:
    """Handles errors, retries, and recovery for the master processor."""
    
    def __init__(self, max_retries: int = 3, retry_delay: int = 5):
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.errors: List[ErrorInfo] = []
        self.logger = logging.getLogger(__name__)
    
    def categorize_error(self, exception: Exception, stage: str) -> ErrorCategory:
        """Categorize an error based on its type and context."""
        error_msg = str(exception).lower()
        
        # Network errors
        if any(keyword in error_msg for keyword in [
            "network", "connection", "timeout", "dns", "socket", 
            "urllib", "requests", "http", "ssl", "certificate"
        ]):
            return ErrorCategory.NETWORK_ERROR
        
        # API errors
        if any(keyword in error_msg for keyword in [
            "api", "quota", "rate limit", "unauthorized", "forbidden",
            "gemini", "openai", "huggingface", "token"
        ]):
            return ErrorCategory.API_ERROR
        
        # Processing errors
        if any(keyword in error_msg for keyword in [
            "cuda", "memory", "whisper", "transcription", "diarization",
            "audio", "model", "gpu", "device"
        ]):
            return ErrorCategory.PROCESSING_ERROR
        
        # System errors
        if any(keyword in error_msg for keyword in [
            "permission", "disk", "space", "file not found", "directory",
            "access denied", "path"
        ]):
            return ErrorCategory.SYSTEM_ERROR
        
        # Default to validation error
        return ErrorCategory.VALIDATION_ERROR
    
    def get_error_suggestion(self, error_info: ErrorInfo) -> str:
        """Get a helpful suggestion for resolving an error."""
        category = error_info.category
        message = error_info.message.lower()
        
        if category == ErrorCategory.NETWORK_ERROR:
            if "timeout" in message:
                return "Check your internet connection and try again. Consider using --retry-delay to increase wait time."
            elif "dns" in message:
                return "Check your DNS settings and internet connection."
            else:
                return "Verify your internet connection and try again. If the problem persists, the service may be temporarily unavailable."
        
        elif category == ErrorCategory.API_ERROR:
            if "quota" in message or "rate limit" in message:
                return "API quota exceeded. Wait a few minutes before retrying, or check your API usage limits."
            elif "unauthorized" in message or "token" in message:
                return "Check your API key configuration. Ensure the key is valid and has the necessary permissions."
            else:
                return "API error occurred. Check your API key and try again."
        
        elif category == ErrorCategory.PROCESSING_ERROR:
            if "cuda" in message or "gpu" in message:
                return "GPU error detected. Try using --cpu flag to force CPU processing, or check your CUDA installation."
            elif "memory" in message:
                return "Out of memory. Try using a smaller Whisper model (--whisper-model base) or process shorter audio files."
            elif "model" in message:
                return "Model loading error. Check that all required dependencies are installed and models can be downloaded."
            else:
                return "Processing error occurred. Check your audio file format and try a different Whisper model size."
        
        elif category == ErrorCategory.SYSTEM_ERROR:
            if "permission" in message or "access denied" in message:
                return "Permission denied. Check file/directory permissions or run with administrator privileges."
            elif "disk" in message or "space" in message:
                return "Insufficient disk space. Free up space and try again."
            elif "file not found" in message:
                return "File not found. Check that the input file exists and the path is correct."
            else:
                return "System error occurred. Check file permissions and available disk space."
        
        else:  # VALIDATION_ERROR
            return "Input validation failed. Check your input format and try again."
    
    def should_retry(self, error_info: ErrorInfo) -> bool:
        """Determine if an error should be retried."""
        if error_info.retry_count >= self.max_retries:
            return False
        
        # Don't retry validation errors
        if error_info.category == ErrorCategory.VALIDATION_ERROR:
            return False
        
        # Don't retry certain system errors
        if error_info.category == ErrorCategory.SYSTEM_ERROR:
            message = error_info.message.lower()
            if any(keyword in message for keyword in ["permission", "access denied", "file not found"]):
                return False
        
        # Don't retry certain API errors
        if error_info.category == ErrorCategory.API_ERROR:
            message = error_info.message.lower()
            if any(keyword in message for keyword in ["unauthorized", "forbidden", "invalid"]):
                return False
        
        return True
    
    def calculate_retry_delay(self, retry_count: int) -> float:
        """Calculate delay before retry using exponential backoff."""
        base_delay = self.retry_delay
        # Exponential backoff: 5, 10, 20, 40, 80 seconds
        return base_delay * (2 ** min(retry_count, 4))
    
    def handle_error(self, exception: Exception, stage: str, context: str = "") -> ErrorInfo:
        """Handle an error and create error info."""
        category = self.categorize_error(exception, stage)
        
        error_info = ErrorInfo(
            category=category,
            message=str(exception),
            stage=stage,
            timestamp=time.time(),
            traceback_info=traceback.format_exc(),
            retry_count=0
        )
        
        error_info.suggestion = self.get_error_suggestion(error_info)
        self.errors.append(error_info)
        
        # Log the error
        context_str = f" ({context})" if context else ""
        self.logger.error(f"Error in {stage}{context_str}: {exception}")
        self.logger.debug(f"Traceback: {error_info.traceback_info}")
        
        return error_info
    
    def retry_with_backoff(self, func: Callable, *args, stage: str = "", context: str = "", **kwargs) -> Any:
        """Execute a function with retry logic and exponential backoff."""
        last_error = None
        
        for attempt in range(self.max_retries + 1):
            try:
                return func(*args, **kwargs)
            
            except Exception as e:
                last_error = e
                error_info = self.handle_error(e, stage, context)
                error_info.retry_count = attempt
                
                if attempt < self.max_retries and self.should_retry(error_info):
                    delay = self.calculate_retry_delay(attempt)
                    self.logger.info(f"Retrying in {delay} seconds (attempt {attempt + 1}/{self.max_retries})...")
                    time.sleep(delay)
                else:
                    break
        
        # If we get here, all retries failed
        raise last_error
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get a summary of all errors that occurred."""
        if not self.errors:
            return {"total_errors": 0, "categories": {}}
        
        category_counts = {}
        for error in self.errors:
            category = error.category.value
            category_counts[category] = category_counts.get(category, 0) + 1
        
        return {
            "total_errors": len(self.errors),
            "categories": category_counts,
            "latest_error": {
                "message": self.errors[-1].message,
                "stage": self.errors[-1].stage,
                "suggestion": self.errors[-1].suggestion
            }
        }
    
    def format_error_report(self) -> str:
        """Format a human-readable error report."""
        if not self.errors:
            return "No errors occurred during processing."
        
        lines = [f"Processing completed with {len(self.errors)} error(s):"]
        lines.append("")
        
        for i, error in enumerate(self.errors, 1):
            lines.append(f"{i}. {error.stage}: {error.message}")
            if error.suggestion:
                lines.append(f"   💡 Suggestion: {error.suggestion}")
            lines.append("")
        
        return "\n".join(lines)
