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

# Color mappings for Todoist labels
# Based on the official Todoist API documentation
TODOIST_COLOR_MAP = {
    # Official Todoist color names (IDs 30-49)
    'berry_red': 'red',          # #B8255F
    'red': 'red',                # #DC4C3E
    'orange': 'orange3',         # #C77100
    'yellow': 'yellow',          # #B29104
    'olive_green': 'green',      # #949C31
    'lime_green': 'lime',        # #65A33A
    'green': 'green',            # #369307
    'mint_green': 'green',       # #42A393
    'teal': 'cyan',              # #148FAD
    'sky_blue': 'cyan',          # #319DC0
    'light_blue': 'blue',        # #6988A4
    'blue': 'blue',              # #4180FF
    'grape': 'purple',           # #692EC2
    'violet': 'purple',          # #CA3FEE
    'lavender': 'magenta',       # #A4698C
    'magenta': 'magenta',        # #E05095
    'salmon': 'red',             # #C9766F
    'charcoal': 'grey',          # #808080
    'grey': 'grey',              # #999999
    'taupe': 'brown',            # #8F7A69
    # Alternative spellings for compatibility
    'gray': 'grey',
}
