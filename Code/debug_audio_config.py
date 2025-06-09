from pathlib import Path
from Audio_Generation.config import AudioGenerationConfig

print("Testing Audio_Generation config path calculation...")
print(f"Current working directory: {Path.cwd()}")
print(f"Config file location: {Path(__file__)}")

config_file = Path(__file__).parent / "Audio_Generation" / "config.py"
print(f"Config module location: {config_file}")

# Calculate project root like the config does
project_root = config_file.parent.parent.parent
print(f"Calculated project root: {project_root}")
print(f"Expected Content path: {project_root / 'Content'}")

try:
    config = AudioGenerationConfig()
    print(f"Actual content_root: {config.file_settings.content_root}")
    print(f"Content directory exists: {Path(config.file_settings.content_root).exists()}")
except Exception as e:
    print(f"Error creating config: {e}")
