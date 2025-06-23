"""Centralized keybinding definitions for the Todoist TUI.

This module contains all keybinding configurations for the main app and modal screens.
Having them centralized makes it easier to maintain consistency and modify bindings.
"""

from typing import List, Tuple

# Type alias for keybinding tuples: (key, action, description)
Keybinding = Tuple[str, str, str]

# Common navigation bindings used across multiple screens
COMMON_NAVIGATION: List[Keybinding] = [
    ("j", "down", ""),           # Hidden from footer but functional
    ("k", "up", ""),             # Hidden from footer but functional  
    ("g", "top", ""),            # Hidden from footer but functional
    ("G", "bottom", ""),         # Hidden from footer but functional
]

# Common modal screen bindings
COMMON_MODAL: List[Keybinding] = [
    ("escape", "dismiss", "Cancel"),
    ("q", "dismiss", "Cancel"),
]

# Main application keybindings
MAIN_APP: List[Keybinding] = [
    ("q", "quit", "Quit"),
    ("r", "refresh", "Refresh"),
    ("d", "complete_task", "Complete"),
    ("D", "delete_task", "Delete"),
    ("a", "add_task", "Add"),
    ("e", "edit_task", "Edit"),
    ("p", "select_project", "Project"),
    ("P", "change_task_project", "Move"),
    ("l", "manage_labels", "Labels"),
    ("f", "show_filter_modal", "Filter"),
] + COMMON_NAVIGATION

# Project selection screen
PROJECT_SELECT: List[Keybinding] = [
    ("enter", "select_project", "Select"),
] + COMMON_MODAL + COMMON_NAVIGATION

# Project change screen (with fuzzy filtering)
CHANGE_PROJECT: List[Keybinding] = [
    ("escape", "dismiss", "Cancel"),
    ("ctrl+c", "dismiss", "Cancel"),
    ("tab", "toggle_focus", "Toggle Focus"),
    ("enter", "select", "Select Project"),
]

# Add task screen
ADD_TASK: List[Keybinding] = [
    ("escape", "dismiss", "Cancel"),
    ("ctrl+c", "dismiss", "Cancel"),
    ("enter", "add_task", "Add Task"),
]

# Edit task screen
EDIT_TASK: List[Keybinding] = [
    ("escape", "dismiss", "Cancel"),
    ("ctrl+c", "dismiss", "Cancel"),
    ("enter", "update_task", "Update Task"),
]

# Label management screen
LABEL_MANAGEMENT: List[Keybinding] = [
    ("space", "toggle_label", "Toggle Label"),
    ("a", "add_label", "Add Label"),
    ("enter", "apply_changes", "Apply Changes"),
    ("/", "focus_filter", "Filter Labels"),
    ("tab", "toggle_focus", "Toggle Focus"),
] + COMMON_MODAL + COMMON_NAVIGATION

# Filter selection screen
FILTER_SELECT: List[Keybinding] = [
    ("escape", "cancel", "Cancel"),
    ("q", "cancel", "Cancel"),
    ("enter", "select_filter", "Select"),
    ("r", "refresh_filters", "Refresh"),
    ("j", "cursor_down", ""),
    ("k", "cursor_up", ""),
]

# Delete confirmation screen (simple modal)
DELETE_CONFIRM: List[Keybinding] = COMMON_MODAL


def get_keybindings(screen_name: str) -> List[Keybinding]:
    """
    Get keybindings for a specific screen.
    
    Args:
        screen_name: Name of the screen/component
        
    Returns:
        List of keybinding tuples
        
    Raises:
        ValueError: If screen_name is not recognized
    """
    keybinding_map = {
        "main_app": MAIN_APP,
        "project_select": PROJECT_SELECT,
        "change_project": CHANGE_PROJECT,
        "add_task": ADD_TASK,
        "edit_task": EDIT_TASK,
        "label_management": LABEL_MANAGEMENT,
        "filter_select": FILTER_SELECT,
        "delete_confirm": DELETE_CONFIRM,
    }
    
    if screen_name not in keybinding_map:
        raise ValueError(f"Unknown screen name: {screen_name}")
    
    return keybinding_map[screen_name]


def get_all_keybindings() -> dict:
    """
    Get all keybindings organized by screen.
    
    Returns:
        Dictionary mapping screen names to their keybindings
    """
    return {
        "main_app": MAIN_APP,
        "project_select": PROJECT_SELECT,
        "change_project": CHANGE_PROJECT,
        "add_task": ADD_TASK,
        "edit_task": EDIT_TASK,
        "label_management": LABEL_MANAGEMENT,
        "filter_select": FILTER_SELECT,
        "delete_confirm": DELETE_CONFIRM,
    }


def validate_keybindings() -> List[str]:
    """
    Validate keybindings for conflicts or issues.
    
    Returns:
        List of validation warnings/errors
    """
    warnings = []
    all_bindings = get_all_keybindings()
    
    # Check for duplicate actions within each screen
    for screen_name, bindings in all_bindings.items():
        keys = [binding[0] for binding in bindings]
        actions = [binding[1] for binding in bindings]
        
        # Check for duplicate keys
        if len(keys) != len(set(keys)):
            duplicates = [key for key in set(keys) if keys.count(key) > 1]
            warnings.append(f"{screen_name}: Duplicate keys: {duplicates}")
        
        # Check for duplicate actions
        if len(actions) != len(set(actions)):
            duplicates = [action for action in set(actions) if actions.count(action) > 1]
            warnings.append(f"{screen_name}: Duplicate actions: {duplicates}")
    
    return warnings


# Convenience functions for common keybinding patterns
def add_help_binding(bindings: List[Keybinding]) -> List[Keybinding]:
    """Add a help binding to a list of keybindings."""
    return bindings + [("?", "show_help", "Help")]


def add_search_binding(bindings: List[Keybinding]) -> List[Keybinding]:
    """Add a search binding to a list of keybindings."""
    return bindings + [("/", "search", "Search")]


def customize_binding_description(bindings: List[Keybinding], key: str, new_description: str) -> List[Keybinding]:
    """
    Customize the description of a specific keybinding.
    
    Args:
        bindings: List of keybindings to modify
        key: The key to modify
        new_description: New description for the key
        
    Returns:
        Modified list of keybindings
    """
    modified_bindings = []
    for binding_key, action, description in bindings:
        if binding_key == key:
            modified_bindings.append((binding_key, action, new_description))
        else:
            modified_bindings.append((binding_key, action, description))
    return modified_bindings
