"""Utility functions for the Todoist TUI."""

import logging
import re
from typing import Optional, Tuple

from ..config import TODOIST_COLOR_MAP

logger = logging.getLogger(__name__)


def format_label_with_color(label_identifier: str, label_name_map: dict, label_color_map: dict, label_by_name: dict) -> str:
    """Format a label with its color using rich markup."""
    # Try to get the label name (works for both ID and name lookups)
    label_name = label_name_map.get(label_identifier) or label_by_name.get(label_identifier, label_identifier)
    
    # Try to get the color - first by ID, then by looking up the ID from name
    label_color = None
    if label_identifier in label_color_map:
        label_color = label_color_map[label_identifier]
    else:
        # Find the label ID by name to get its color
        for label_id, name in label_name_map.items():
            if name == label_identifier:
                label_color = label_color_map.get(label_id)
                break
    
    # Debug logging
    logger.info(f"Label '{label_identifier}' -> name: '{label_name}', color: '{label_color}'")
    
    if label_color and label_color in TODOIST_COLOR_MAP:
        rich_color = TODOIST_COLOR_MAP[label_color]
        formatted = f"[{rich_color}]{label_name}[/{rich_color}]"
        logger.info(f"Formatted label: '{formatted}'")
        return formatted
    else:
        logger.info(f"No color mapping found for '{label_color}', returning plain: '{label_name}'")
        return label_name


def parse_natural_language_date(content: str) -> Tuple[str, Optional[str]]:
    """
    Parse natural language date patterns from task content.
    
    Returns:
        Tuple of (cleaned_content, due_string) where due_string is None if no date found.
    """
    # Look for natural language date patterns
    date_patterns = [
        r'\b(today|tomorrow|yesterday)\b',
        r'\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b',
        r'\b\d{1,2}[/-]\d{1,2}([/-]\d{2,4})?\b',
        r'\bat \d{1,2}:\d{2}( ?[ap]m)?\b',
        r'\b(next|this) (week|month|year)\b',
        r'\bin \d+ (day|week|month|year)s?\b'
    ]
    
    # Check if content contains date-like patterns
    has_date = any(re.search(pattern, content, re.IGNORECASE) for pattern in date_patterns)
    
    if has_date:
        # Extract potential due date string from the end or specific patterns
        # This is a simplified approach - in a full implementation,
        # you might want more sophisticated parsing
        due_match = re.search(
            r'\b(due|by|on|at|tomorrow|today|next \w+|this \w+|\d{1,2}[/-]\d{1,2}|\w+day)\b.*$', 
            content, 
            re.IGNORECASE
        )
        if due_match:
            due_string = due_match.group(0)
            # Remove the due date part from content to get clean task name
            cleaned_content = content[:due_match.start()].strip()
            return cleaned_content, due_string
    
    return content, None


def extract_task_id_from_row_key(row_key) -> Optional[str]:
    """Extract the actual task ID from a DataTable row key object."""
    if row_key is None:
        return None
    
    # Extract the actual task ID from the RowKey object
    if hasattr(row_key, 'value') and row_key.value is not None:
        return str(row_key.value)
    else:
        return str(row_key)


def validate_api_token(token: Optional[str]) -> bool:
    """Validate that the API token is properly set."""
    return token is not None and isinstance(token, str) and len(token.strip()) > 0
