"""
JSON Schema Validation Framework for Two-Pass AI Quality Control System

This module provides comprehensive validation functions for all pipeline data structures
to ensure format consistency across Pass 1, Pass 2, and rebuttal verification stages.

Author: APM Implementation Agent
Created: 2025-01-13
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple
import jsonschema
from jsonschema import validate, ValidationError, Draft202012Validator, RefResolver
import logging

# Set up logging
logger = logging.getLogger(__name__)

class JSONSchemaValidator:
    """
    Comprehensive JSON schema validation framework for the YouTube pipeline.
    
    Provides validation functions for all pipeline stages with detailed error reporting
    and schema loading capabilities.
    """
    
    def __init__(self, schemas_dir: Optional[str] = None):
        """
        Initialize the validator with schema directory path.
        
        Args:
            schemas_dir: Path to the JSON schemas directory. If None, uses default location.
        """
        if schemas_dir is None:
            # Default to the schemas directory relative to this file
            current_dir = Path(__file__).parent.parent
            self.schemas_dir = current_dir / "Content_Analysis" / "JSON_Schemas"
        else:
            self.schemas_dir = Path(schemas_dir)
            
        self.schemas = {}
        self._load_schemas()
    
    def _load_schemas(self) -> None:
        """Load all JSON schemas from the schemas directory."""
        schema_files = {
            'original_analysis_results': 'original_analysis_results_schema.json',
            'unified_podcast_script': 'unified_podcast_script_schema.json',
            'final_filtered_analysis_results': 'final_filtered_analysis_results_schema.json',
            'verified_unified_script': 'verified_unified_script_schema.json',
            'quality_control_results': 'quality_control_results_schemas.json'
        }
        
        for schema_name, filename in schema_files.items():
            schema_path = self.schemas_dir / filename
            try:
                with open(schema_path, 'r', encoding='utf-8') as f:
                    self.schemas[schema_name] = json.load(f)
                logger.info(f"Loaded schema: {schema_name}")
            except FileNotFoundError:
                logger.error(f"Schema file not found: {schema_path}")
                raise FileNotFoundError(f"Required schema file not found: {schema_path}")
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in schema file {schema_path}: {e}")
                raise ValueError(f"Invalid JSON in schema file {schema_path}: {e}")
    
    def _validate_with_detailed_errors(
        self, 
        data: Union[Dict, List], 
        schema: Dict,
        data_description: str
    ) -> Tuple[bool, List[str]]:
        """
        Validate data against schema with detailed error reporting.
        
        Args:
            data: Data to validate
            schema: JSON schema to validate against
            data_description: Description of the data being validated
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        try:
            # Create a reference resolver to handle $ref in schemas
            resolver = RefResolver(
                base_uri=f"file://{self.schemas_dir}/",
                referrer=schema,
                store=self.schemas
            )
            
            # Use Draft 2020-12 validator with resolver
            validator = Draft202012Validator(schema, resolver=resolver)
            validator.validate(data)
            logger.info(f"Validation successful for {data_description}")
            return True, []
            
        except ValidationError as e:
            error_messages = [f"Validation failed for {data_description}:"]
            
            # Main error
            error_path = " -> ".join(str(p) for p in e.absolute_path) if e.absolute_path else "root"
            error_messages.append(f"  Path: {error_path}")
            error_messages.append(f"  Error: {e.message}")
            error_messages.append(f"  Failed value: {e.instance}")
            error_messages.append(f"  Schema rule: {e.schema}")
            
            # Additional context errors
            for suberror in sorted(e.context, key=lambda x: x.absolute_path):
                sub_path = " -> ".join(str(p) for p in suberror.absolute_path)
                error_messages.append(f"  Sub-error at {sub_path}: {suberror.message}")
            
            logger.error(f"Validation failed for {data_description}: {e.message}")
            return False, error_messages
            
        except Exception as e:
            error_messages = [
                f"Unexpected validation error for {data_description}: {str(e)}"
            ]
            logger.error(f"Unexpected validation error for {data_description}: {e}")
            return False, error_messages
    
    def validate_pass1_output(
        self, 
        analysis_results: Union[List[Dict], str, Path]
    ) -> Tuple[bool, List[str]]:
        """
        Validate Pass 1 analysis results output.
        
        Args:
            analysis_results: Analysis results data or file path
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        if isinstance(analysis_results, (str, Path)):
            try:
                with open(analysis_results, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError) as e:
                return False, [f"Error loading Pass 1 output file: {e}"]
        else:
            data = analysis_results
            
        return self._validate_with_detailed_errors(
            data, 
            self.schemas['original_analysis_results'],
            "Pass 1 Analysis Results"
        )
    
    def validate_pass2_input(
        self, 
        analysis_results: Union[List[Dict], str, Path]
    ) -> Tuple[bool, List[str]]:
        """
        Validate Pass 2 input (should match Pass 1 output format).
        
        Args:
            analysis_results: Analysis results data or file path
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        # Pass 2 input should match Pass 1 output format
        return self.validate_pass1_output(analysis_results)
    
    def validate_pass2_output(
        self, 
        filtered_results: Union[List[Dict], str, Path]
    ) -> Tuple[bool, List[str]]:
        """
        Validate Pass 2 filtered analysis results output.
        
        Args:
            filtered_results: Filtered analysis results data or file path
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        if isinstance(filtered_results, (str, Path)):
            try:
                with open(filtered_results, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError) as e:
                return False, [f"Error loading Pass 2 output file: {e}"]
        else:
            data = filtered_results
            
        return self._validate_with_detailed_errors(
            data,
            self.schemas['final_filtered_analysis_results'], 
            "Pass 2 Filtered Analysis Results"
        )
    
    def validate_script_input(
        self, 
        script_data: Union[Dict, str, Path]
    ) -> Tuple[bool, List[str]]:
        """
        Validate script generation input (unified podcast script).
        
        Args:
            script_data: Script data or file path
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        if isinstance(script_data, (str, Path)):
            try:
                with open(script_data, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError) as e:
                return False, [f"Error loading script input file: {e}"]
        else:
            data = script_data
            
        return self._validate_with_detailed_errors(
            data,
            self.schemas['unified_podcast_script'],
            "Unified Podcast Script Input"
        )
    
    def validate_verified_script_output(
        self, 
        verified_script: Union[Dict, str, Path]
    ) -> Tuple[bool, List[str]]:
        """
        Validate verified script output with verification metadata.
        
        Args:
            verified_script: Verified script data or file path
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        if isinstance(verified_script, (str, Path)):
            try:
                with open(verified_script, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError) as e:
                return False, [f"Error loading verified script file: {e}"]
        else:
            data = verified_script
            
        return self._validate_with_detailed_errors(
            data,
            self.schemas['verified_unified_script'],
            "Verified Unified Script Output"
        )
    
    def validate_quality_control_results(
        self,
        qc_data: Union[Dict, str, Path],
        result_type: str
    ) -> Tuple[bool, List[str]]:
        """
        Validate quality control results data.
        
        Args:
            qc_data: Quality control data or file path
            result_type: Type of QC result (quality_scores, filtering_decisions, etc.)
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        if isinstance(qc_data, (str, Path)):
            try:
                with open(qc_data, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError) as e:
                return False, [f"Error loading quality control results file: {e}"]
        else:
            data = qc_data
        
        # Get the specific schema definition
        qc_schemas = self.schemas['quality_control_results']
        if 'definitions' not in qc_schemas:
            return False, [f"Quality control schemas malformed - missing definitions"]
            
        schema_key = f"{result_type}_schema"
        if schema_key not in qc_schemas['definitions']:
            valid_types = list(qc_schemas['definitions'].keys())
            return False, [f"Invalid result_type '{result_type}'. Valid types: {valid_types}"]
            
        schema = qc_schemas['definitions'][schema_key]
        
        return self._validate_with_detailed_errors(
            data,
            schema,
            f"Quality Control Results ({result_type})"
        )
    
    def validate_pipeline_stage(
        self,
        data: Union[Dict, List, str, Path],
        stage: str
    ) -> Tuple[bool, List[str]]:
        """
        Validate data for a specific pipeline stage.
        
        Args:
            data: Data to validate or file path
            stage: Pipeline stage ('pass1_output', 'pass2_input', 'pass2_output', 
                  'script_input', 'verified_script_output')
                  
        Returns:
            Tuple of (is_valid, error_messages)
        """
        stage_validators = {
            'pass1_output': self.validate_pass1_output,
            'pass2_input': self.validate_pass2_input, 
            'pass2_output': self.validate_pass2_output,
            'script_input': self.validate_script_input,
            'verified_script_output': self.validate_verified_script_output
        }
        
        if stage not in stage_validators:
            valid_stages = list(stage_validators.keys())
            return False, [f"Invalid stage '{stage}'. Valid stages: {valid_stages}"]
            
        return stage_validators[stage](data)
    
    def halt_on_validation_failure(
        self,
        data: Union[Dict, List, str, Path],
        stage: str
    ) -> None:
        """
        Validate data and halt pipeline execution on validation failures.
        
        Args:
            data: Data to validate or file path
            stage: Pipeline stage identifier
            
        Raises:
            ValueError: If validation fails with descriptive error message
        """
        is_valid, error_messages = self.validate_pipeline_stage(data, stage)
        
        if not is_valid:
            error_msg = f"Pipeline halted due to validation failure at stage '{stage}':\n"
            error_msg += "\n".join(error_messages)
            logger.critical(f"Pipeline halted at stage {stage} due to validation failure")
            raise ValueError(error_msg)
        
        logger.info(f"Validation passed for stage: {stage}")


# Convenience functions for direct use
def create_validator(schemas_dir: Optional[str] = None) -> JSONSchemaValidator:
    """
    Create a JSONSchemaValidator instance.
    
    Args:
        schemas_dir: Optional path to schemas directory
        
    Returns:
        JSONSchemaValidator instance
    """
    return JSONSchemaValidator(schemas_dir)


def validate_file(file_path: str, stage: str, schemas_dir: Optional[str] = None) -> bool:
    """
    Validate a JSON file for a specific pipeline stage.
    
    Args:
        file_path: Path to JSON file to validate
        stage: Pipeline stage identifier
        schemas_dir: Optional path to schemas directory
        
    Returns:
        True if validation passes, False otherwise
    """
    validator = create_validator(schemas_dir)
    is_valid, error_messages = validator.validate_pipeline_stage(file_path, stage)
    
    if not is_valid:
        for error in error_messages:
            logger.error(error)
    
    return is_valid


def halt_pipeline_on_invalid_data(
    data: Union[Dict, List, str, Path], 
    stage: str,
    schemas_dir: Optional[str] = None
) -> None:
    """
    Halt pipeline execution if data validation fails.
    
    Args:
        data: Data to validate or file path
        stage: Pipeline stage identifier
        schemas_dir: Optional path to schemas directory
        
    Raises:
        ValueError: If validation fails
    """
    validator = create_validator(schemas_dir)
    validator.halt_on_validation_failure(data, stage)


if __name__ == "__main__":
    # Example usage and basic testing
    validator = create_validator()
    print("JSON Schema Validator initialized successfully")
    print(f"Loaded schemas: {list(validator.schemas.keys())}")