"""Utility functions for the Todoist TUI."""

import logging
import re
from typing import Optional, Tuple, Dict, Any

from ..colors import get_label_color, get_filter_color, get_project_color
from rich.text import Text

logger = logging.getLogger(__name__)


def format_project_option_with_color(project_id: str, project_name: str, project_color_map: Dict[str, str]) -> Text:
    """Format a project name for use in OptionList or similar widgets with color support."""
    project_color = project_color_map.get(project_id)
    
    if project_color:
        # Use Rich Text object with the exact Todoist hex color
        hex_color = get_project_color(project_color)
        # Create colored text for the project name with bullet
        project_text = Text(f"● {project_name}", style=hex_color)
        logger.debug(f"Created Rich Text for project option: '{project_name}' with color: '{hex_color}'")
        return project_text
    else:
        logger.debug(f"No color found for project '{project_id}', returning plain text: '{project_name}'")
        return Text(f"● {project_name}")


def format_project_with_color(project_id: str, project_name_map: Dict[str, str], project_color_map: Dict[str, str]) -> Text:
    """Format a project with its color using Rich Text object for DataTable."""
    project_name = project_name_map.get(project_id, f"Unknown Project ({project_id})")
    project_color = project_color_map.get(project_id)
    
    logger.debug(f"Project '{project_id}' -> name: '{project_name}', color: '{project_color}'")
    
    if project_color:
        # Use Rich Text object with the exact Todoist hex color
        hex_color = get_project_color(project_color)
        # Create colored text for the project name
        project_text = Text(project_name, style=f"bold {hex_color}")
        logger.debug(f"Created Rich Text object for project: '{project_name}' with color: '{hex_color}'")
        return project_text
    else:
        logger.debug(f"No color found for project '{project_id}', returning plain text: '{project_name}'")
        return Text(project_name, style="bold")


def format_label_with_color(label_identifier: str, label_name_map: Dict[str, str], label_color_map: Dict[str, str], label_by_name: Dict[str, str]) -> Text:
    """Format a label with its color using Rich Text object for DataTable."""
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
    
    if label_color:
        # Use Rich Text object with the exact Todoist hex color
        hex_color = get_label_color(label_color)
        # Create separate Text objects for the bullet and name, both with the same color
        bullet_text = Text("●", style=hex_color)
        name_text = Text(f" {label_name}", style=hex_color)
        # Combine them
        combined_text = bullet_text + name_text
        logger.info(f"Created Rich Text object for label: '{label_name}' with color: '{hex_color}'")
        return combined_text
    else:
        logger.info(f"No color found for label '{label_identifier}', returning plain text: '{label_name}'")
        return Text(f"● {label_name}")


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


def extract_task_id_from_row_key(row_key: Any) -> Optional[str]:
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
    return token is not None and len(token.strip()) > 0


def format_filter_with_color(filter_name: str, filter_color: str):
    """Format a filter name with its color using Rich Text object for DataTable."""
    logger.info(f"Formatting filter '{filter_name}' with color '{filter_color}'")
    
    if filter_color:
        # Use Rich Text object with the exact Todoist hex color
        hex_color = get_filter_color(filter_color)
        # Create separate Text objects for the bullet and name
        bullet_text = Text("●", style=hex_color)
        name_text = Text(f" {filter_name}")
        # Combine them
        combined_text = bullet_text + name_text
        logger.info(f"Created Rich Text object for filter: '{filter_name}' with color: '{hex_color}'")
        return combined_text
    else:
        logger.info(f"No color found for filter '{filter_name}', returning plain text")
        return Text(f"● {filter_name}")
