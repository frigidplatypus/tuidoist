"""Configuration settings for the Todoist TUI."""

import os
import logging

# API Configuration
TODOIST_API_TOKEN = os.environ.get("TODOIST_API_TOKEN")

# Logging Configuration
LOG_FILE = "tui.log"
LOG_LEVEL = logging.INFO
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Setup logging
logging.basicConfig(filename=LOG_FILE, level=LOG_LEVEL, filemode="w", format=LOG_FORMAT)

# Import shared color utilities
from tuidoist.colors import (
    TODOIST_TO_TEXTUAL_COLOR_MAP,
    TODOIST_TO_TEXTUAL_NAMED_COLOR_MAP,
    get_todoist_color,
    get_label_color,
    get_filter_color,
    get_project_color,
    format_colored_text,
)

# Legacy color mapping for backward compatibility
# This is deprecated - use tuidoist.colors functions instead
TODOIST_COLOR_MAP = TODOIST_TO_TEXTUAL_NAMED_COLOR_MAP
