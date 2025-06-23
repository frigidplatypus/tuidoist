"""
Shared color mapping utilities for Todoist TUI.

This module provides centralized color mapping between Todoist's official color names
and Textual's supported color system. It maps Todoist's color names to the best
available Textual color or hex value.

Based on:
- Todoist API colors: https://developer.todoist.com/guides/#colors
- Textual color system: https://textual.textualize.io/css_types/color/
"""

from typing import Dict


# Official Todoist color palette with hex values
# Source: https://developer.todoist.com/guides/#colors
TODOIST_OFFICIAL_COLORS = {
    # ID 30-49 from Todoist API
    'berry_red': '#B8255F',
    'red': '#DC4C3E',
    'orange': '#C77100',
    'yellow': '#B29104',
    'olive_green': '#949C31',
    'lime_green': '#65A33A',
    'green': '#369307',
    'mint_green': '#42A393',
    'teal': '#148FAD',
    'sky_blue': '#319DC0',
    'light_blue': '#6988A4',
    'blue': '#4180FF',
    'grape': '#692EC2',
    'violet': '#CA3FEE',
    'lavender': '#A4698C',
    'magenta': '#E05095',
    'salmon': '#C9766F',
    'charcoal': '#808080',
    'grey': '#999999',
    'taupe': '#8F7A69',
}

# Mapping from Todoist color names to Textual-compatible colors
# This prioritizes exact hex values where possible, falling back to named colors
# that provide the closest visual match
TODOIST_TO_TEXTUAL_COLOR_MAP = {
    # Use exact hex values from Todoist - Textual supports hex colors
    'berry_red': '#B8255F',
    'red': '#DC4C3E',
    'orange': '#C77100',
    'yellow': '#B29104',
    'olive_green': '#949C31',
    'lime_green': '#65A33A',
    'green': '#369307',
    'mint_green': '#42A393',
    'teal': '#148FAD',
    'sky_blue': '#319DC0',
    'light_blue': '#6988A4',
    'blue': '#4180FF',
    'grape': '#692EC2',
    'violet': '#CA3FEE',
    'lavender': '#A4698C',
    'magenta': '#E05095',
    'salmon': '#C9766F',
    'charcoal': '#808080',
    'grey': '#999999',
    'taupe': '#8F7A69',
    
    # Alternative spellings for compatibility
    'gray': '#999999',  # Same as grey
}

# Fallback mapping to Textual named colors for cases where hex isn't supported
# or for simpler styling contexts
TODOIST_TO_TEXTUAL_NAMED_COLOR_MAP = {
    'berry_red': 'red',
    'red': 'red',
    'orange': 'orange3',
    'yellow': 'yellow',
    'olive_green': 'dark_green',
    'lime_green': 'green',
    'green': 'green',
    'mint_green': 'dark_turquoise',
    'teal': 'dark_turquoise',
    'sky_blue': 'sky_blue1',
    'light_blue': 'light_blue',
    'blue': 'blue',
    'grape': 'dark_violet',
    'violet': 'magenta',
    'lavender': 'plum1',
    'magenta': 'magenta',
    'salmon': 'light_coral',
    'charcoal': 'grey',
    'grey': 'grey',
    'taupe': 'tan',
    
    # Alternative spellings for compatibility
    'gray': 'grey',
}


def get_todoist_color(color_name: str, use_hex: bool = True) -> str:
    """
    Get the Textual-compatible color for a Todoist color name.
    
    Args:
        color_name: The Todoist color name (e.g., 'berry_red', 'teal', 'grey')
        use_hex: If True, return hex colors when available; if False, return named colors
    
    Returns:
        A Textual-compatible color string (hex or named color)
    
    Examples:
        >>> get_todoist_color('teal')
        '#148FAD'
        >>> get_todoist_color('teal', use_hex=False)
        'cyan'
        >>> get_todoist_color('unknown_color')
        'white'
    """
    if not color_name:
        return 'white'
    
    # Normalize color name
    color_name = color_name.lower().strip()
    
    if use_hex:
        color = TODOIST_TO_TEXTUAL_COLOR_MAP.get(color_name)
        if color:
            return color
    
    # Fallback to named colors
    color = TODOIST_TO_TEXTUAL_NAMED_COLOR_MAP.get(color_name)
    if color:
        return color
    
    # Ultimate fallback
    return 'white'


def get_label_color(color_name: str) -> str:
    """
    Get the Textual color for a Todoist label.
    
    Args:
        color_name: The Todoist color name from the label
    
    Returns:
        A Textual-compatible color string
    """
    return get_todoist_color(color_name, use_hex=True)


def get_filter_color(color_name: str) -> str:
    """
    Get the Textual color for a Todoist filter.
    
    Args:
        color_name: The Todoist color name from the filter
    
    Returns:
        A Textual-compatible color string
    """
    return get_todoist_color(color_name, use_hex=True)


def get_project_color(color_name: str) -> str:
    """
    Get the Textual color for a Todoist project.
    
    Args:
        color_name: The Todoist color name from the project
    
    Returns:
        A Textual-compatible color string
    """
    return get_todoist_color(color_name, use_hex=True)


def format_colored_text(text: str, color_name: str) -> str:
    """
    Format text with Todoist color using Rich markup.
    
    Args:
        text: The text to color
        color_name: The Todoist color name
    
    Returns:
        Rich markup formatted string
    
    Examples:
        >>> format_colored_text("My Filter", "teal")
        '[color=#148FAD]My Filter[/color]'
    """
    if not color_name:
        return text
    
    color = get_todoist_color(color_name, use_hex=True)
    return f'[color={color}]{text}[/color]'


def is_valid_todoist_color(color_name: str) -> bool:
    """
    Check if a color name is a valid Todoist color.
    
    Args:
        color_name: The color name to check
    
    Returns:
        True if the color name is valid, False otherwise
    """
    if not color_name:
        return False
    
    color_name = color_name.lower().strip()
    return color_name in TODOIST_TO_TEXTUAL_COLOR_MAP


def get_all_todoist_colors() -> Dict[str, str]:
    """
    Get all available Todoist colors with their hex values.
    
    Returns:
        Dictionary mapping color names to hex values
    """
    return TODOIST_OFFICIAL_COLORS.copy()


def get_color_preview(color_name: str) -> str:
    """
    Get a preview of a color for display in the UI.
    
    Args:
        color_name: The Todoist color name
    
    Returns:
        A formatted string showing the color name and visual indicator
    """
    if not color_name:
        return "No color"
    
    color = get_todoist_color(color_name, use_hex=True)
    # Use a colored bullet point as a visual indicator
    return f'[color={color}]●[/color] {color_name}'
