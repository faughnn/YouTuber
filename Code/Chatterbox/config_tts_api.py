# Configuration file for Chatterbox TTS
# Modify these values to customize your TTS generation

# Text to be converted to speech
TEXT_TO_CONVERT = "Alright, 'at least 50%' of internet interactions are bots? That's a bold claim, even for the internet. While bot activity is certainly a concern, especially in political discourse and social media, the idea that half of all online engagement is non-human, pushing 'narratives' with 'no rules,' is a massive oversimplification that borders on fear-mongering. Reputable studies on bot activity, like those from the Pew Research Center or various cybersecurity firms, typically estimate bot traffic to be significant, but rarely, if ever, reaching 50% of *interactions* in a way that implies pervasive, malicious control over all discourse. Many bots are benign, like search engine crawlers or customer service bots. The claim that 'no rules' exist is also misleading; platforms have terms of service, and governments are increasingly looking into regulations. This kind of blanket statement fosters a deep, unhealthy distrust in all digital information, making it harder for people to discern legitimate news from actual propaganda. It's the digital equivalent of saying 'don't trust anyone,' which is great for paranoia, terrible for informed citizenship."

# Speech Parameters
EXAGGERATION = 0.7      # Emotion intensity (0.25-2.0)
                        # 0.3-0.4: Professional, neutral
                        # 0.5: Default balanced  
                        # 0.7-0.8: More expressive
                        # 1.0+: Very dramatic

CFG_WEIGHT = 0.7        # Pace control (0.0-1.0)
                        # 0.2-0.3:  Slower, deliberate
                        # 0.5: Default pace
                        # 0.7-0.8: Faster speech

TEMPERATURE = 0.3       # Sampling randomness (0.05-5.0)
                        # 0.4-0.6: More consistent
                        # 0.8: Default balance
                        # 1.0+: More creative/random

# API Configuration
API_BASE_URL = "http://localhost:4123"
OUTPUT_FILE = f"speech_E{EXAGGERATION}_C{CFG_WEIGHT}_T{TEMPERATURE}.wav"

# Optional: Path to custom voice file for voice cloning
# Set to None to use default voice
# Example: CUSTOM_VOICE_FILE = "my_voice.mp3"
CUSTOM_VOICE_FILE = None

# GPU Configuration
# The Docker setup will automatically use GPU if available
USE_GPU = True
DEVICE = "auto"  # auto, cuda, mps, cpu

# Audio Quality Validation Configuration
ENABLE_AUDIO_VALIDATION = True      # Enable/disable audio quality checks
MAX_RETRIES = 20                     # Maximum retry attempts for silent clips
SILENCE_THRESHOLD_DB = -40          # dB threshold for silence detection (-50 to -20)
MIN_SILENCE_DURATION_MS = 2000      # Minimum silence duration to trigger retry (milliseconds)
MAX_SILENCE_RATIO = 0.1             # Maximum allowed ratio of silence to total audio (0.0-1.0)

# Silence detection explanation:
# SILENCE_THRESHOLD_DB: -40dB is a good balance (quieter = more sensitive)
# MIN_SILENCE_DURATION_MS: 2000ms = 2 seconds of continuous silence triggers retry
# MAX_SILENCE_RATIO: 0.3 means if more than 30% of audio is silence, retry generation
