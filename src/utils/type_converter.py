"""Utility functions for converting numpy/pandas types to native Python types."""

import numpy as np
import pandas as pd
from typing import Any, Dict, List, Union


def convert_to_native(value: Any) -> Any:
    """
    Convert numpy/pandas types to native Python types for JSON serialization.
    
    Args:
        value: Value to convert (can be numpy scalar, pandas type, etc.)
        
    Returns:
        Native Python type (int, float, str, bool, etc.)
    """
    # Handle None
    if value is None:
        return None
    
    # Handle numpy integer types
    if isinstance(value, (np.integer, np.int_, np.int8, np.int16, np.int32, np.int64)):
        return int(value)
    
    # Handle numpy float types
    if isinstance(value, (np.floating, np.float_, np.float16, np.float32, np.float64)):
        return float(value)
    
    # Handle numpy bool
    if isinstance(value, np.bool_):
        return bool(value)
    
    # Handle numpy string
    if isinstance(value, np.str_):
        return str(value)
    
    # Handle pandas types
    if isinstance(value, (pd.Timestamp, pd.Timedelta)):
        return str(value)
    
    # Handle pandas NA
    if pd.isna(value):
        return None
    
    # Handle lists
    if isinstance(value, list):
        return [convert_to_native(item) for item in value]
    
    # Handle dictionaries
    if isinstance(value, dict):
        return {key: convert_to_native(val) for key, val in value.items()}
    
    # Handle numpy arrays
    if isinstance(value, np.ndarray):
        return value.tolist()
    
    # Return as-is if already native type
    return value


def sanitize_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively convert all numpy/pandas types in a dictionary to native Python types.
    
    Args:
        data: Dictionary potentially containing numpy/pandas types
        
    Returns:
        Dictionary with all values converted to native Python types
    """
    result = {}
    for key, value in data.items():
        result[key] = convert_to_native(value)
    return result


def sanitize_list(data: List[Any]) -> List[Any]:
    """
    Convert all numpy/pandas types in a list to native Python types.
    
    Args:
        data: List potentially containing numpy/pandas types
        
    Returns:
        List with all values converted to native Python types
    """
    return [convert_to_native(item) for item in data]

