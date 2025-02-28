from typing import Any, Dict, List, Optional, Type, TypeVar, Union
from pydantic import BaseModel
from decimal import Decimal
import json

T = TypeVar('T', bound=BaseModel)

def format_amount(value: Union[int, float, str]) -> Decimal:
    """Format a numeric value as a Decimal."""
    return Decimal(str(value))

def validate_response(response: Any, model: Type[T]) -> T:
    """Validate and convert an RPC response to a model instance."""
    if isinstance(response, dict):
        return model.model_validate(response)
    raise ValueError(f"Expected dict response, got {type(response)}")

def validate_list_response(response: Any, model: Type[T]) -> List[T]:
    """Validate and convert a list response to a list of model instances."""
    if isinstance(response, list):
        return [model.model_validate(item) for item in response]
    raise ValueError(f"Expected list response, got {type(response)}")

def validate_dict_response(response: Any, model: Type[T]) -> Dict[str, T]:
    """Validate and convert a dictionary response to a dictionary of model instances."""
    if isinstance(response, dict):
        return {key: model.model_validate(value) for key, value in response.items()}
    raise ValueError(f"Expected dict response, got {type(response)}")

def format_command_args(*args: Any) -> List[str]:
    """Format command arguments for RPC calls."""
    formatted_args = []
    for arg in args:
        if arg is None:
            continue
        if isinstance(arg, bool):
            formatted_args.append("true" if arg else "false")
        elif isinstance(arg, (dict, list)):
            # Convert to JSON string and properly escape quotes
            formatted_args.append(json.dumps(arg))
        else:
            formatted_args.append(str(arg))
    return formatted_args 