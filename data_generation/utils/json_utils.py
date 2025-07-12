"""
JSON processing utilities for the data generation project.
Handles JSON extraction, validation, and repair.
"""

import json
import re
from typing import Dict, Any, Optional, Tuple
import json_repair


def extract_json_from_text(text: str) -> Optional[str]:
    """
    Extract the first valid JSON object from text.
    
    Args:
        text: Text containing JSON
        
    Returns:
        Extracted JSON string or None if not found
    """
    if not text:
        return None
        
    # Find the outermost curly braces
    first_brace = text.find('{')
    last_brace = text.rfind('}')
    
    if first_brace == -1 or last_brace == -1 or last_brace <= first_brace:
        return None
        
    return text[first_brace:last_brace + 1]


def parse_json_safe(json_str: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    Safely parse JSON with automatic repair if needed.
    
    Args:
        json_str: JSON string to parse
        
    Returns:
        Tuple of (parsed_object, error_message)
        If successful, error_message is None
    """
    if not json_str:
        return None, "Empty JSON string"
        
    # First try standard json.loads
    try:
        return json.loads(json_str), None
    except json.JSONDecodeError as e:
        first_error = f"Standard JSON parsing failed: {str(e)}"
        
    # Try json_repair if standard parsing fails
    try:
        repaired = json_repair.loads(json_str, skip_json_loads=True)
        return repaired, None
    except Exception as e:
        return None, f"{first_error}. JSON repair also failed: {str(e)}"


def validate_json_structure(data: Dict[str, Any], required_fields: list) -> Tuple[bool, list]:
    """
    Validate that a JSON object contains required fields.
    
    Args:
        data: JSON data to validate
        required_fields: List of required field names
        
    Returns:
        Tuple of (is_valid, missing_fields)
    """
    if not isinstance(data, dict):
        return False, ["Data is not a dictionary"]
        
    missing_fields = [field for field in required_fields if field not in data]
    return len(missing_fields) == 0, missing_fields


def clean_json_string(json_str: str) -> str:
    """
    Clean common issues in JSON strings.
    
    Args:
        json_str: JSON string to clean
        
    Returns:
        Cleaned JSON string
    """
    if not json_str:
        return json_str
        
    # Remove trailing commas before closing braces/brackets
    json_str = re.sub(r',\s*}', '}', json_str)
    json_str = re.sub(r',\s*]', ']', json_str)
    
    # Remove BOM if present
    if json_str.startswith('\ufeff'):
        json_str = json_str[1:]
        
    return json_str.strip()


def save_json(data: Any, filepath: str, indent: int = 2) -> None:
    """
    Save JSON data to file with proper formatting.
    
    Args:
        data: Data to save (dict, list, or any JSON-serializable object)
        filepath: Path to save file
        indent: Indentation level
    """
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=indent)


def load_json(filepath: str) -> Dict[str, Any]:
    """
    Load JSON data from file.
    
    Args:
        filepath: Path to JSON file
        
    Returns:
        Loaded JSON data
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def merge_json_objects(base: Dict[str, Any], update: Dict[str, Any], deep: bool = True) -> Dict[str, Any]:
    """
    Merge two JSON objects.
    
    Args:
        base: Base dictionary
        update: Dictionary with updates
        deep: Whether to do deep merge
        
    Returns:
        Merged dictionary
    """
    if not deep:
        return {**base, **update}
        
    result = base.copy()
    
    for key, value in update.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_json_objects(result[key], value, deep=True)
        else:
            result[key] = value
            
    return result 