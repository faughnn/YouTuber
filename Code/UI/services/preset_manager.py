"""
Workflow Preset Management Service
YouTube Pipeline UI - Phase 5: Audio & Preset System

Comprehensive preset management for saving, loading, and managing workflow configurations.
Provides JSON-based file storage with database integration and validation.

Created: June 20, 2025
Agent: Agent_Preset_Audio  
Task Reference: Phase 5, Task 5.1 - Workflow Preset System
"""

import json
import uuid
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import shutil

from flask import current_app
from database.models import db, PresetConfiguration
from database.utils import PresetManager as DBPresetManager


@dataclass
class PresetValidationResult:
    """Result of preset validation operation."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]


class PresetFileManager:
    """Manages JSON file storage for workflow presets."""
    
    def __init__(self, presets_dir: str = None):
        """Initialize preset file manager."""
        if presets_dir is None:
            # Default to Code/UI/presets/ directory
            base_dir = Path(__file__).parent.parent
            presets_dir = base_dir / "presets"
        
        self.presets_dir = Path(presets_dir)
        self.presets_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories for organization
        (self.presets_dir / "system").mkdir(exist_ok=True)
        (self.presets_dir / "custom").mkdir(exist_ok=True)
        (self.presets_dir / "templates").mkdir(exist_ok=True)
        (self.presets_dir / "backup").mkdir(exist_ok=True)
    
    def save_preset_file(self, preset_name: str, preset_data: Dict[str, Any], 
                        category: str = "custom") -> Tuple[bool, str]:
        """
        Save preset to JSON file.
        
        Args:
            preset_name: Name of the preset
            preset_data: Complete preset configuration
            category: Preset category (system, custom, templates)
            
        Returns:
            Tuple of (success, file_path_or_error)
        """
        try:
            # Sanitize filename
            safe_name = self._sanitize_filename(preset_name)
            file_path = self.presets_dir / category / f"{safe_name}.json"
            
            # Add file metadata
            file_data = {
                "metadata": {
                    "name": preset_name,
                    "category": category,
                    "created_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat(),
                    "version": "1.0",
                    "format_version": "5.1"
                },
                "configuration": preset_data
            }
            
            # Write to file with backup
            self._write_with_backup(file_path, file_data)
            
            return True, str(file_path)
            
        except Exception as e:
            return False, f"Failed to save preset file: {str(e)}"
    
    def load_preset_file(self, preset_name: str, category: str = None) -> Tuple[bool, Dict[str, Any]]:
        """
        Load preset from JSON file.
        
        Args:
            preset_name: Name of the preset
            category: Optional category to search in
            
        Returns:
            Tuple of (success, preset_data_or_error)
        """
        try:
            file_path = self._find_preset_file(preset_name, category)
            if not file_path:
                return False, {"error": f"Preset file not found: {preset_name}"}
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Validate file format
            if not self._validate_file_format(data):
                return False, {"error": "Invalid preset file format"}
            
            return True, data
            
        except Exception as e:
            return False, {"error": f"Failed to load preset file: {str(e)}"}
    
    def delete_preset_file(self, preset_name: str, category: str = None) -> Tuple[bool, str]:
        """Delete preset file with backup."""
        try:
            file_path = self._find_preset_file(preset_name, category)
            if not file_path:
                return False, f"Preset file not found: {preset_name}"
            
            # Create backup before deletion
            backup_path = self.presets_dir / "backup" / f"{preset_name}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
            shutil.copy2(file_path, backup_path)
            
            # Delete original file
            file_path.unlink()
            
            return True, f"Preset deleted, backup saved to: {backup_path}"
            
        except Exception as e:
            return False, f"Failed to delete preset file: {str(e)}"
    
    def list_preset_files(self, category: str = None) -> List[Dict[str, Any]]:
        """List available preset files."""
        files = []
        
        try:
            search_dirs = [category] if category else ["system", "custom", "templates"]
            
            for cat in search_dirs:
                cat_dir = self.presets_dir / cat
                if cat_dir.exists():
                    for file_path in cat_dir.glob("*.json"):
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                data = json.load(f)
                            
                            if self._validate_file_format(data):
                                files.append({
                                    "name": data["metadata"]["name"],
                                    "category": cat,
                                    "file_path": str(file_path),
                                    "created_at": data["metadata"].get("created_at"),
                                    "updated_at": data["metadata"].get("updated_at"),
                                    "version": data["metadata"].get("version", "1.0")
                                })
                        except Exception as e:
                            current_app.logger.warning(f"Failed to read preset file {file_path}: {e}")
            
            return sorted(files, key=lambda x: x["name"])
            
        except Exception as e:
            current_app.logger.error(f"Failed to list preset files: {e}")
            return []
    
    def _sanitize_filename(self, name: str) -> str:
        """Sanitize preset name for filename use."""
        # Replace invalid characters
        invalid_chars = '<>:"/\\|?*'
        sanitized = ''.join(c for c in name if c not in invalid_chars)
        # Replace spaces with underscores
        sanitized = sanitized.replace(' ', '_')
        # Limit length
        return sanitized[:50]
    
    def _find_preset_file(self, preset_name: str, category: str = None) -> Optional[Path]:
        """Find preset file by name."""
        safe_name = self._sanitize_filename(preset_name)
        
        search_dirs = [category] if category else ["system", "custom", "templates"]
        
        for cat in search_dirs:
            file_path = self.presets_dir / cat / f"{safe_name}.json"
            if file_path.exists():
                return file_path
        
        return None
    
    def _validate_file_format(self, data: Dict[str, Any]) -> bool:
        """Validate preset file format."""
        return (
            isinstance(data, dict) and
            "metadata" in data and
            "configuration" in data and
            isinstance(data["metadata"], dict) and
            "name" in data["metadata"]
        )
    
    def _write_with_backup(self, file_path: Path, data: Dict[str, Any]):
        """Write file with automatic backup."""
        # Create backup if file exists
        if file_path.exists():
            backup_path = self.presets_dir / "backup" / f"{file_path.stem}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
            shutil.copy2(file_path, backup_path)
        
        # Write new file
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)


class PresetValidator:
    """Validates preset configurations for integrity and compatibility."""
    
    REQUIRED_FIELDS = {
        "stage_selection": list,
        "segment_mode": str,
        "prompt_references": dict,
        "audio_method": str,
        "output_settings": dict
    }
    
    VALID_STAGES = list(range(1, 8))  # Stages 1-7
    VALID_SEGMENT_MODES = ["auto", "manual"]
    VALID_AUDIO_METHODS = ["tts", "voice_clone", "manual"]
    
    @classmethod
    def validate_preset(cls, preset_config: Dict[str, Any]) -> PresetValidationResult:
        """
        Comprehensive preset validation.
        
        Args:
            preset_config: Preset configuration to validate
            
        Returns:
            PresetValidationResult with validation status and messages
        """
        errors = []
        warnings = []
        
        # Check required fields
        for field, expected_type in cls.REQUIRED_FIELDS.items():
            if field not in preset_config:
                errors.append(f"Missing required field: {field}")
            elif not isinstance(preset_config[field], expected_type):
                errors.append(f"Invalid type for {field}: expected {expected_type.__name__}")
        
        if errors:
            return PresetValidationResult(False, errors, warnings)
        
        # Validate stage selection
        stage_errors, stage_warnings = cls._validate_stages(preset_config["stage_selection"])
        errors.extend(stage_errors)
        warnings.extend(stage_warnings)
        
        # Validate segment mode
        if preset_config["segment_mode"] not in cls.VALID_SEGMENT_MODES:
            errors.append(f"Invalid segment_mode: {preset_config['segment_mode']}. Must be one of {cls.VALID_SEGMENT_MODES}")
        
        # Validate audio method
        if preset_config["audio_method"] not in cls.VALID_AUDIO_METHODS:
            errors.append(f"Invalid audio_method: {preset_config['audio_method']}. Must be one of {cls.VALID_AUDIO_METHODS}")
        
        # Validate prompt references
        prompt_errors, prompt_warnings = cls._validate_prompt_references(preset_config["prompt_references"])
        errors.extend(prompt_errors)
        warnings.extend(prompt_warnings)
        
        # Validate output settings
        output_errors, output_warnings = cls._validate_output_settings(preset_config["output_settings"])
        errors.extend(output_errors)
        warnings.extend(output_warnings)
        
        return PresetValidationResult(len(errors) == 0, errors, warnings)
    
    @classmethod
    def _validate_stages(cls, stages: List[int]) -> Tuple[List[str], List[str]]:
        """Validate stage selection."""
        errors = []
        warnings = []
        
        if not stages:
            errors.append("Stage selection cannot be empty")
            return errors, warnings
        
        # Check for invalid stages
        invalid_stages = [s for s in stages if s not in cls.VALID_STAGES]
        if invalid_stages:
            errors.append(f"Invalid stages: {invalid_stages}. Valid stages are {cls.VALID_STAGES}")
        
        # Check for logical stage dependencies
        if 4 in stages and 3 not in stages:
            warnings.append("Stage 4 (Segment Selection) selected without Stage 3 (Segment Identification)")
        
        if 5 in stages and 4 not in stages:
            warnings.append("Stage 5 (Audio Generation) selected without Stage 4 (Segment Selection)")
        
        if 6 in stages and 5 not in stages:
            warnings.append("Stage 6 (Video Compilation) selected without Stage 5 (Audio Generation)")
        
        if 7 in stages and 6 not in stages:
            warnings.append("Stage 7 (Final Output) selected without Stage 6 (Video Compilation)")
        
        return errors, warnings
    
    @classmethod
    def _validate_prompt_references(cls, prompt_refs: Dict[str, str]) -> Tuple[List[str], List[str]]:
        """Validate prompt references."""
        errors = []
        warnings = []
        
        # Required prompt references based on common workflow
        if not prompt_refs:
            warnings.append("No prompt references specified")
            return errors, warnings
        
        # Check that referenced files use proper naming convention
        for key, value in prompt_refs.items():
            if not isinstance(value, str):
                errors.append(f"Prompt reference '{key}' must be a string filename")
            elif not value.endswith('.txt'):
                warnings.append(f"Prompt reference '{key}' should reference a .txt file")
        
        return errors, warnings
    
    @classmethod
    def _validate_output_settings(cls, output_settings: Dict[str, Any]) -> Tuple[List[str], List[str]]:
        """Validate output settings."""
        errors = []
        warnings = []
        
        # Check required output settings
        required_settings = ["format", "quality"]
        for setting in required_settings:
            if setting not in output_settings:
                warnings.append(f"Missing recommended output setting: {setting}")
        
        # Validate format
        if "format" in output_settings:
            valid_formats = ["mp4", "json", "txt"]
            if output_settings["format"] not in valid_formats:
                warnings.append(f"Unusual output format: {output_settings['format']}")
        
        # Validate quality
        if "quality" in output_settings:
            valid_qualities = ["low", "standard", "high"]
            if output_settings["quality"] not in valid_qualities:
                warnings.append(f"Invalid quality setting: {output_settings['quality']}")
        
        return errors, warnings


class PresetManager:
    """
    Comprehensive preset management system.
    
    Integrates database storage with JSON file management and provides
    validation, versioning, and workflow integration capabilities.
    """
    
    def __init__(self):
        """Initialize preset manager."""
        self.file_manager = PresetFileManager()
        self.validator = PresetValidator()
    
    def create_preset(self, name: str, configuration: Dict[str, Any], 
                     description: str = None, category: str = "custom") -> Tuple[bool, Dict[str, Any]]:
        """
        Create new preset with validation and dual storage.
        
        Args:
            name: Preset name
            configuration: Preset configuration dictionary
            description: Optional description
            category: Preset category
            
        Returns:
            Tuple of (success, result_dict)
        """
        try:
            # Validate configuration
            validation_result = self.validator.validate_preset(configuration)
            if not validation_result.is_valid:
                return False, {
                    "error": "Preset validation failed",
                    "validation_errors": validation_result.errors,
                    "validation_warnings": validation_result.warnings
                }
            
            # Check if preset name already exists
            existing = DBPresetManager.get_preset_by_name(name)
            if existing:
                return False, {"error": f"Preset with name '{name}' already exists"}
            
            # Save to database
            db_preset = DBPresetManager.create_preset(
                name=name,
                configuration=configuration,
                description=description,
                category=category
            )
            
            # Save to JSON file
            file_success, file_result = self.file_manager.save_preset_file(
                name, configuration, category
            )
            
            if not file_success:
                # Rollback database creation if file save fails
                DBPresetManager.delete_preset(db_preset.preset_id)
                return False, {"error": f"Failed to save preset file: {file_result}"}
            
            return True, {
                "preset_id": db_preset.preset_id,
                "name": name,
                "category": category,
                "file_path": file_result,
                "validation_warnings": validation_result.warnings
            }
            
        except Exception as e:
            return False, {"error": f"Failed to create preset: {str(e)}"}
    
    def load_preset(self, preset_id: str = None, preset_name: str = None) -> Tuple[bool, Dict[str, Any]]:
        """
        Load preset by ID or name.
        
        Args:
            preset_id: Database preset ID
            preset_name: Preset name
            
        Returns:
            Tuple of (success, preset_data)
        """
        try:
            # Get from database
            if preset_id:
                db_preset = DBPresetManager.get_preset(preset_id)
            elif preset_name:
                db_preset = DBPresetManager.get_preset_by_name(preset_name)
            else:
                return False, {"error": "Must provide either preset_id or preset_name"}
            
            if not db_preset:
                return False, {"error": "Preset not found in database"}
            
            # Load from JSON file for additional metadata
            file_success, file_data = self.file_manager.load_preset_file(
                db_preset.preset_name, db_preset.category
            )
            
            # Combine database and file data
            result = {
                "preset_id": db_preset.preset_id,
                "name": db_preset.preset_name,
                "description": db_preset.description,
                "category": db_preset.category,
                "configuration": db_preset.configuration_json,
                "usage_count": db_preset.usage_count,
                "last_used_at": db_preset.last_used_at.isoformat() if db_preset.last_used_at else None,
                "created_at": db_preset.created_at.isoformat(),
                "updated_at": db_preset.updated_at.isoformat()
            }
            
            # Add file metadata if available
            if file_success:
                result["file_metadata"] = file_data.get("metadata", {})
            
            return True, result
            
        except Exception as e:
            return False, {"error": f"Failed to load preset: {str(e)}"}
    
    def update_preset(self, preset_id: str, configuration: Dict[str, Any] = None,
                     description: str = None, **kwargs) -> Tuple[bool, Dict[str, Any]]:
        """Update existing preset."""
        try:
            # Get existing preset
            db_preset = DBPresetManager.get_preset(preset_id)
            if not db_preset:
                return False, {"error": "Preset not found"}
            
            # Validate new configuration if provided
            if configuration:
                validation_result = self.validator.validate_preset(configuration)
                if not validation_result.is_valid:
                    return False, {
                        "error": "Configuration validation failed",
                        "validation_errors": validation_result.errors
                    }
            
            # Update database
            update_data = {}
            if configuration:
                update_data["configuration_json"] = configuration
            if description:
                update_data["description"] = description
            
            db_success = DBPresetManager.update_preset(preset_id, **update_data)
            if not db_success:
                return False, {"error": "Failed to update database"}
            
            # Update file if configuration changed
            if configuration:
                file_success, file_result = self.file_manager.save_preset_file(
                    db_preset.preset_name, configuration, db_preset.category
                )
                if not file_success:
                    return False, {"error": f"Failed to update preset file: {file_result}"}
            
            return True, {"message": "Preset updated successfully"}
            
        except Exception as e:
            return False, {"error": f"Failed to update preset: {str(e)}"}
    
    def delete_preset(self, preset_id: str) -> Tuple[bool, Dict[str, Any]]:
        """Delete preset from both database and file storage."""
        try:
            # Get preset info before deletion
            db_preset = DBPresetManager.get_preset(preset_id)
            if not db_preset:
                return False, {"error": "Preset not found"}
            
            # Delete from file storage
            file_success, file_message = self.file_manager.delete_preset_file(
                db_preset.preset_name, db_preset.category
            )
            
            # Delete from database
            db_success = DBPresetManager.delete_preset(preset_id)
            
            if not db_success:
                return False, {"error": "Failed to delete from database"}
            
            return True, {
                "message": "Preset deleted successfully",
                "file_backup": file_message if file_success else "File backup failed"
            }
            
        except Exception as e:
            return False, {"error": f"Failed to delete preset: {str(e)}"}
    
    def list_presets(self, category: str = None) -> List[Dict[str, Any]]:
        """List all available presets."""
        try:
            # Get from database
            db_presets = DBPresetManager.get_all_presets(category)
            
            # Combine with file information
            result = []
            for preset in db_presets:
                preset_data = {
                    "preset_id": preset.preset_id,
                    "name": preset.preset_name,
                    "description": preset.description,
                    "category": preset.category,
                    "usage_count": preset.usage_count,
                    "last_used_at": preset.last_used_at.isoformat() if preset.last_used_at else None,
                    "created_at": preset.created_at.isoformat(),
                    "updated_at": preset.updated_at.isoformat(),
                    "stage_names": preset.get_stage_names()
                }
                result.append(preset_data)
            
            return result
            
        except Exception as e:
            current_app.logger.error(f"Failed to list presets: {e}")
            return []
    
    def use_preset(self, preset_id: str) -> Tuple[bool, Dict[str, Any]]:
        """Mark preset as used and return configuration for pipeline execution."""
        try:
            # Load preset
            success, preset_data = self.load_preset(preset_id=preset_id)
            if not success:
                return False, preset_data
            
            # Update usage statistics
            DBPresetManager.use_preset(preset_id)
            
            # Return configuration ready for pipeline execution
            return True, {
                "preset_id": preset_id,
                "name": preset_data["name"],
                "configuration": preset_data["configuration"],
                "usage_count": preset_data["usage_count"] + 1
            }
            
        except Exception as e:
            return False, {"error": f"Failed to use preset: {str(e)}"}
    
    def export_preset(self, preset_id: str, export_path: str) -> Tuple[bool, str]:
        """Export preset to specified path."""
        try:
            success, preset_data = self.load_preset(preset_id=preset_id)
            if not success:
                return False, preset_data["error"]
            
            # Create export data
            export_data = {
                "export_metadata": {
                    "exported_at": datetime.utcnow().isoformat(),
                    "source_system": "YouTube Pipeline UI",
                    "format_version": "5.1"
                },
                "preset_data": preset_data
            }
            
            export_path = Path(export_path)
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            return True, f"Preset exported to: {export_path}"
            
        except Exception as e:
            return False, f"Failed to export preset: {str(e)}"
    
    def import_preset(self, import_path: str, overwrite: bool = False) -> Tuple[bool, Dict[str, Any]]:
        """Import preset from file."""
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            # Validate import format
            if "preset_data" not in import_data:
                return False, {"error": "Invalid import file format"}
            
            preset_data = import_data["preset_data"]
            
            # Check if preset exists
            existing = DBPresetManager.get_preset_by_name(preset_data["name"])
            if existing and not overwrite:
                return False, {"error": f"Preset '{preset_data['name']}' already exists. Use overwrite=True to replace."}
            
            # Delete existing if overwriting
            if existing and overwrite:
                self.delete_preset(existing.preset_id)
            
            # Create new preset
            return self.create_preset(
                name=preset_data["name"],
                configuration=preset_data["configuration"],
                description=preset_data.get("description"),
                category=preset_data.get("category", "custom")
            )
            
        except Exception as e:
            return False, {"error": f"Failed to import preset: {str(e)}"}
    
    def get_preset_statistics(self) -> Dict[str, Any]:
        """Get preset usage statistics."""
        try:
            all_presets = DBPresetManager.get_all_presets()
            
            stats = {
                "total_presets": len(all_presets),
                "categories": {},
                "usage_stats": {
                    "most_used": None,
                    "total_usage": 0,
                    "never_used": 0
                },
                "recent_activity": []
            }
            
            # Category breakdown
            for preset in all_presets:
                category = preset.category
                if category not in stats["categories"]:
                    stats["categories"][category] = 0
                stats["categories"][category] += 1
                
                # Usage statistics
                stats["usage_stats"]["total_usage"] += preset.usage_count
                if preset.usage_count == 0:
                    stats["usage_stats"]["never_used"] += 1
                
                # Most used preset
                if (stats["usage_stats"]["most_used"] is None or 
                    preset.usage_count > stats["usage_stats"]["most_used"]["usage_count"]):
                    stats["usage_stats"]["most_used"] = {
                        "name": preset.preset_name,
                        "usage_count": preset.usage_count
                    }
                
                # Recent activity
                if preset.last_used_at:
                    stats["recent_activity"].append({
                        "name": preset.preset_name,
                        "last_used": preset.last_used_at.isoformat(),
                        "usage_count": preset.usage_count
                    })
            
            # Sort recent activity
            stats["recent_activity"].sort(
                key=lambda x: x["last_used"], reverse=True
            )
            stats["recent_activity"] = stats["recent_activity"][:10]  # Top 10
            
            return stats
            
        except Exception as e:
            current_app.logger.error(f"Failed to get preset statistics: {e}")
            return {"error": str(e)}
