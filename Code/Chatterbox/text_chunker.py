"""
Chatterbox Text Chunking Module

This module provides intelligent text chunking functionality to overcome 
ChatterboxTTS 40-second output limitation by splitting long text into 
manageable chunks while preserving sentence boundaries and providing
seamless audio concatenation.

Based on proven research solution - chunks text at sentence boundaries
using 280 character default size to stay well under 40-second limit.
"""

import logging
import re
import time
from typing import List, Tuple, Optional, TYPE_CHECKING
from pathlib import Path

# Type checking imports
if TYPE_CHECKING:
    import torch

# Audio processing imports
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    torch = None
    TORCH_AVAILABLE = False

logger = logging.getLogger(__name__)


def chunk_text(text: str, max_chars: int = 280) -> List[str]:
    """
    Split text into chunks while preserving sentence boundaries.
      Uses proven algorithm with regex pattern r'(?<=[.!?])\\s+' for sentence 
    boundary detection. Default chunk size of 280 characters ensures
    each chunk stays well under ChatterboxTTS 40-second limit.
    
    Args:
        text: Input text to chunk
        max_chars: Maximum characters per chunk (default 280)
        
    Returns:
        List of text chunks, each preserving sentence boundaries
        
    Raises:
        ValueError: If text is empty or max_chars is too small
    """
    if not text or not text.strip():
        logger.warning("Empty text provided to chunk_text")
        return []
    
    if max_chars < 50:
        raise ValueError("max_chars must be at least 50 to handle reasonable sentences")
    
    text = text.strip()
    
    # If text is already short enough, return as single chunk
    if len(text) <= max_chars:
        logger.debug(f"Text length {len(text)} <= {max_chars}, returning single chunk")
        return [text]
    
    logger.debug(f"Chunking text of length {len(text)} into chunks of max {max_chars} chars")
    
    # Split text by sentence endings using proven regex pattern
    sentences = re.split(r'(?<=[.!?])\s+', text)
    logger.debug(f"Text split into {len(sentences)} sentences")
    
    chunks = []
    current_chunk = ""
    
    for i, sentence in enumerate(sentences):
        sentence = sentence.strip()
        if not sentence:
            continue
            
        # Check if adding this sentence would exceed max_chars
        potential_chunk = current_chunk + (" " if current_chunk else "") + sentence
        
        if len(potential_chunk) <= max_chars:
            # Safe to add this sentence to current chunk
            current_chunk = potential_chunk
        else:
            # Current chunk would be too long, save it and start new one
            if current_chunk:
                chunks.append(current_chunk)
                logger.debug(f"Saved chunk {len(chunks)}: {len(current_chunk)} chars")
            
            # Handle edge case: single sentence longer than max_chars
            if len(sentence) > max_chars:
                logger.warning(f"Sentence {i+1} is {len(sentence)} chars, longer than max_chars {max_chars}")
                # Split long sentence at word boundaries as fallback
                words = sentence.split()
                word_chunk = ""
                for word in words:
                    potential_word_chunk = word_chunk + (" " if word_chunk else "") + word
                    if len(potential_word_chunk) <= max_chars:
                        word_chunk = potential_word_chunk
                    else:
                        if word_chunk:
                            chunks.append(word_chunk)
                            logger.debug(f"Saved word chunk {len(chunks)}: {len(word_chunk)} chars")
                        word_chunk = word
                if word_chunk:
                    current_chunk = word_chunk
                else:
                    current_chunk = ""
            else:
                current_chunk = sentence
    
    # Don't forget the last chunk
    if current_chunk:
        chunks.append(current_chunk)
        logger.debug(f"Saved final chunk {len(chunks)}: {len(current_chunk)} chars")
    
    logger.info(f"Text chunked into {len(chunks)} chunks (avg {sum(len(c) for c in chunks) / len(chunks):.1f} chars each)")
    
    return chunks


def generate_chunked_audio(model, text: str, audio_prompt_path: str, 
                          exaggeration: float, temperature: float, 
                          cfg_weight: float, max_chars: int = 280) -> Tuple[Optional[object], float, bool]:
    """
    Generate audio for long text using intelligent chunking approach.
    
    Splits text into manageable chunks, generates audio for each chunk separately,
    then concatenates all audio tensors into seamless final output. Provides
    progress tracking and duration calculation.
      Args:
        model: Loaded ChatterboxTTS model instance
        text: Input text to convert to speech
        audio_prompt_path: Path to voice training sample
        exaggeration: Voice exaggeration parameter (required)
        temperature: Voice temperature parameter (required)
        cfg_weight: Voice CFG weight parameter (required)
        max_chars: Maximum characters per chunk (default 280)
        
    Returns:
        Tuple of (combined_audio_tensor, total_duration, success_flag)
        
    Raises:
        RuntimeError: If torch is not available or model operations fail
    """
    if not TORCH_AVAILABLE:
        raise RuntimeError("PyTorch not available - required for audio tensor operations")
    
    if not text or not text.strip():
        logger.error("Empty text provided to generate_chunked_audio")
        return None, 0.0, False
    
    if not model:
        logger.error("No model provided to generate_chunked_audio")
        return None, 0.0, False
    
    start_time = time.time()
    text = text.strip()
    
    # Split text into manageable chunks
    chunks = chunk_text(text, max_chars)
    
    if not chunks:
        logger.error("No chunks generated from text")
        return None, 0.0, False
    
    logger.info(f"Generating chunked audio: {len(chunks)} chunks from {len(text)} character text")
    
    chunk_wavs = []
    total_duration = 0.0
    
    try:
        # Generate audio for each chunk
        for i, chunk in enumerate(chunks, 1):
            logger.info(f"Generating chunk {i}/{len(chunks)}: {len(chunk)} chars")
            logger.debug(f"Chunk {i} text preview: {chunk[:50]}...")
            
            # Generate audio for this chunk using same parameters
            wav = model.generate(
                text=chunk,
                audio_prompt_path=audio_prompt_path,
                exaggeration=exaggeration,
                temperature=temperature,
                cfg_weight=cfg_weight
            )
            
            if wav is None:
                logger.error(f"Failed to generate audio for chunk {i}")
                return None, 0.0, False
            
            # Calculate chunk duration (ChatterboxTTS outputs at 24kHz)
            chunk_duration = wav.shape[-1] / 24000.0
            total_duration += chunk_duration
            chunk_wavs.append(wav)
            
            logger.info(f"Chunk {i} completed: {chunk_duration:.1f}s duration")
        
        # Combine all audio chunks using torch.cat for seamless concatenation
        logger.info("Concatenating audio chunks...")
        combined_wav = torch.cat(chunk_wavs, dim=-1)
        
        generation_time = time.time() - start_time
        logger.info(f"Chunked audio generation completed: {total_duration:.1f}s total duration, "
                   f"{generation_time:.1f}s generation time")
        
        return combined_wav, total_duration, True
        
    except Exception as e:
        logger.error(f"Error during chunked audio generation: {e}")
        return None, 0.0, False


def should_use_chunking(text: str, threshold: int = 280) -> bool:
    """
    Determine if text should use chunking based on length threshold.
    
    Args:
        text: Input text to evaluate
        threshold: Character threshold for chunking (default 280)
        
    Returns:
        True if text should be chunked, False for single generation
    """
    if not text:
        return False
    
    return len(text.strip()) > threshold
