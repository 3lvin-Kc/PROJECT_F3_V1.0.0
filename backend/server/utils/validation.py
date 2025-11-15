"""
Validation Utilities
===================
Simple validation functions to replace Pydantic Field constraints.
Used for dataclass validation in the MVP version.
"""

from typing import Any, Union


def validate_confidence(value: float, field_name: str = "confidence") -> float:
    """
    Validate confidence value is between 0.0 and 1.0.
    
    Args:
        value: The confidence value to validate
        field_name: Name of the field for error messages
        
    Returns:
        The validated confidence value
        
    Raises:
        ValueError: If confidence is not between 0.0 and 1.0
    """
    if not isinstance(value, (int, float)):
        raise ValueError(f"{field_name} must be a number")
    
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{field_name} must be between 0.0 and 1.0, got {value}")
    
    return float(value)


def validate_required_string(value: Any, field_name: str) -> str:
    """
    Validate that a value is a non-empty string.
    
    Args:
        value: The value to validate
        field_name: Name of the field for error messages
        
    Returns:
        The validated string value
        
    Raises:
        ValueError: If value is not a valid string
    """
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")
    
    if not value.strip():
        raise ValueError(f"{field_name} cannot be empty")
    
    return value


def validate_optional_string(value: Any, field_name: str) -> Union[str, None]:
    """
    Validate that a value is either None or a string.
    
    Args:
        value: The value to validate
        field_name: Name of the field for error messages
        
    Returns:
        The validated string value or None
        
    Raises:
        ValueError: If value is not None or a valid string
    """
    if value is None:
        return None
    
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string or None")
    
    return value


def validate_positive_int(value: Any, field_name: str) -> int:
    """
    Validate that a value is a positive integer.
    
    Args:
        value: The value to validate
        field_name: Name of the field for error messages
        
    Returns:
        The validated integer value
        
    Raises:
        ValueError: If value is not a positive integer
    """
    if not isinstance(value, int):
        raise ValueError(f"{field_name} must be an integer")
    
    if value < 0:
        raise ValueError(f"{field_name} must be positive, got {value}")
    
    return value
