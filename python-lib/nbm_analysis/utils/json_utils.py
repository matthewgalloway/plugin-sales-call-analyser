import re
import json
from typing import Any


def clean_json_response(text: str) -> str:
    """Clean and extract JSON from AI response

    Args:
        text: Raw text response that may contain JSON

    Returns:
        Cleaned JSON string ready for parsing
    """
    # Remove markdown code blocks
    json_match = re.search(r'```(?:json)?\s*(\{.*\})\s*```', text, re.DOTALL)
    if json_match:
        text = json_match.group(1)
    else:
        # Try to find JSON object directly
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            text = json_match.group(0)

    # Remove trailing commas before closing braces/brackets
    text = re.sub(r',(\s*[}\]])', r'\1', text)

    return text.strip()


def safe_json_loads(text: str) -> Any:
    """Safely load JSON with cleaning

    Args:
        text: Raw text that may contain JSON

    Returns:
        Parsed JSON object

    Raises:
        json.JSONDecodeError: If JSON cannot be parsed
    """
    cleaned = clean_json_response(text)
    return json.loads(cleaned)
