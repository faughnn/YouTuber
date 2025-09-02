
"""
Configuration Manager for the Name Extractor.

This module loads and provides the settings from the 
`Code/Config/name_extractor_rules.json` file.
"""

import json
import os

# Handle imports for both module and direct execution
try:
    from .project_paths import get_config_file
except ImportError:
    # For direct execution, add current directory to path
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from project_paths import get_config_file

# Store the config globally after loading it once to avoid repeated file I/O.
_config = None
# Get config path using centralized path discovery
_config_path = str(get_config_file('name_extractor_rules.json'))

def get_config():
    """
    Loads the configuration from the JSON file if it hasn't been loaded yet,
    and returns the cached configuration.
    
    Returns:
        dict: The configuration dictionary.
    
    Raises:
        FileNotFoundError: If the configuration file cannot be found.
        json.JSONDecodeError: If the configuration file is not valid JSON.
    """
    global _config
    if _config is None:
        if not os.path.exists(_config_path):
            raise FileNotFoundError(f"Configuration file not found at: {_config_path}")
        
        with open(_config_path, 'r', encoding='utf-8') as f:
            _config = json.load(f)
    return _config

def get_setting(key, default=None):
    """
    Gets a value from the 'settings' section of the config.
    """
    config = get_config()
    return config.get("settings", {}).get(key, default)

def get_uploader_rule(uploader_name):
    """
    Gets the rule for a specific uploader.
    """
    config = get_config()
    return config.get("uploader_rules", {}).get(uploader_name)

def get_host_mapping(uploader_name):
    """
    Gets the friendly host name mapping for a specific uploader.
    
    Args:
        uploader_name: The uploader/channel name
        
    Returns:
        str: Mapped host name, or None if no mapping exists
    """
    config = get_config()
    return config.get("host_mappings", {}).get(uploader_name)

def reload_config():
    """
    Forces a reload of the configuration from disk.
    Useful when the config file has been modified.
    """
    global _config
    _config = None
    return get_config()

# Example usage for testing when this file is run directly
if __name__ == '__main__':
    print("Running ConfigManager example...")
    try:
        # Initial load
        config_data = get_config()
        print("Config loaded successfully.")
        
        # Test get_setting
        prompt_setting = get_setting('prompt_for_verification')
        print(f"Setting 'prompt_for_verification': {prompt_setting}")

        # Test get_uploader_rule
        jre_rule = get_uploader_rule('PowerfulJRE')
        print(f"Rule for 'PowerfulJRE': {jre_rule}")

        tucker_rule = get_uploader_rule('Tucker Carlson')
        print(f"Rule for 'Tucker Carlson': {tucker_rule}")

        non_existent_rule = get_uploader_rule('NonExistentChannel')
        print(f"Rule for 'NonExistentChannel': {non_existent_rule}")

        # Test that the config is cached
        print("\nCalling get_config() again to test caching...")
        config_data_2 = get_config()
        if id(config_data) == id(config_data_2):
            print("Confirmed: Configuration is cached (not re-read from file).")
        else:
            print("Warning: Configuration was re-read from file.")

    except Exception as e:
        print(f"An error occurred during the example run: {e}")
