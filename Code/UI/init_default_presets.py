"""
Initialize default presets in the database
This script loads the default preset JSON files and creates database entries for them.
"""

import sys
import os
from pathlib import Path

# Add the Code/UI directory to the path
ui_path = Path(__file__).parent / "Code" / "UI"
sys.path.insert(0, str(ui_path))

from services.preset_manager import PresetManager, PresetFileManager
from app import create_app

def initialize_default_presets():
    """Initialize default presets from JSON files into the database."""
    print("🔧 Initializing default presets...")
    
    # Create Flask app context
    app, socketio = create_app()
    
    with app.app_context():
        preset_manager = PresetManager()
        file_manager = PresetFileManager()
        
        # Get all system presets from files
        system_presets = file_manager.list_preset_files(category="system")
        
        print(f"Found {len(system_presets)} system presets to initialize:")
        
        for preset_file in system_presets:
            print(f"  📁 Loading {preset_file['name']}...")
            
            # Load preset from file
            success, file_data = file_manager.load_preset_file(
                preset_file['name'], 
                preset_file['category']
            )
            
            if not success:
                print(f"    ❌ Failed to load preset file: {file_data}")
                continue
            
            # Check if preset already exists in database
            existing = preset_manager.load_preset(preset_name=preset_file['name'])
            if existing[0]:  # Success means it exists
                print(f"    ⚠️  Preset already exists in database, skipping")
                continue
            
            # Create preset in database
            success, result = preset_manager.create_preset(
                name=file_data['metadata']['name'],
                configuration=file_data['configuration'],
                description=file_data['metadata'].get('description', ''),
                category=file_data['metadata']['category']
            )
            
            if success:
                print(f"    ✅ Created preset in database: {result['preset_id']}")
            else:
                print(f"    ❌ Failed to create preset: {result}")
        
        # Display final statistics
        stats = preset_manager.get_preset_statistics()
        print(f"\n📊 Final statistics:")
        print(f"   Total presets: {stats['total_presets']}")
        print(f"   System presets: {stats['categories'].get('system', 0)}")
        print(f"   Custom presets: {stats['categories'].get('custom', 0)}")
        
        print("\n🎉 Default preset initialization completed!")

if __name__ == "__main__":
    initialize_default_presets()
