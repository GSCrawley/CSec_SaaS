"""
Utility functions for knowledge fabric.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Union

logger = logging.getLogger(__name__)

def convert_neo4j_to_python(value: Any) -> Any:
    """Convert Neo4j types to Python native types.
    
    Args:
        value: Value to convert, can be a single value, dictionary, or list.
        
    Returns:
        Converted value.
    """
    # Handle None
    if value is None:
        return None
    
    # Handle node objects
    if hasattr(value, '__class__') and value.__class__.__name__ == 'Node':
        result = {}
        for key, val in dict(value).items():
            result[key] = convert_neo4j_to_python(val)
        return result
    
    # Handle relationship objects
    if hasattr(value, '__class__') and value.__class__.__name__ == 'Relationship':
        result = {
            'type': value.type,
            'properties': {}
        }
        for key, val in dict(value).items():
            result['properties'][key] = convert_neo4j_to_python(val)
        return result
    
    # Handle path objects
    if hasattr(value, '__class__') and value.__class__.__name__ == 'Path':
        return {
            'nodes': [convert_neo4j_to_python(node) for node in value.nodes],
            'relationships': [convert_neo4j_to_python(rel) for rel in value.relationships]
        }
    
    # Handle datetime objects
    if hasattr(value, '__class__') and value.__class__.__name__ == 'DateTime':
        return datetime(
            year=value.year, 
            month=value.month, 
            day=value.day,
            hour=value.hour,
            minute=value.minute, 
            second=value.second,
            microsecond=value.nanosecond // 1000  # Convert nanoseconds to microseconds
        )
    
    # Handle lists
    if isinstance(value, list):
        return [convert_neo4j_to_python(item) for item in value]
    
    # Handle dictionaries
    if isinstance(value, dict):
        return {k: convert_neo4j_to_python(v) for k, v in value.items()}
    
    # Return other types unchanged
    return value