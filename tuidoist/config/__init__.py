"""Configuration settings for the Todoist TUI."""

import os
import logging
from pathlib import Path
from typing import Optional

def get_config_directory() -> Path:
    """Get the appropriate configuration directory following XDG Base Directory Specification."""
    if os.name == 'nt':  # Windows
        # Use %APPDATA%\tuidoist
        appdata = os.environ.get('APPDATA')
        if appdata:
            config_dir = Path(appdata) / "tuidoist"
        else:
            config_dir = Path.home() / "AppData" / "Roaming" / "tuidoist"
    else:
        # Unix-like systems (Linux, macOS, etc.)
        # Use XDG_CONFIG_HOME or ~/.config (standard)
        xdg_config_home = os.environ.get('XDG_CONFIG_HOME')
        if xdg_config_home:
            config_dir = Path(xdg_config_home) / "tuidoist"
        else:
            config_dir = Path.home() / ".config" / "tuidoist"
    
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir

def load_api_token() -> Optional[str]:
    """Load Todoist API token from multiple sources in priority order."""
    
    # 1. For development: Check .env file in project directory first
    project_root = Path(__file__).parent.parent.parent
    env_file = project_root / ".env"
    if env_file.exists():
        try:
            with open(env_file) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        if key.strip() == "TODOIST_API_TOKEN":
                            token = value.strip().strip('"\'')
                            if token:
                                return token
        except Exception:
            pass  # Continue to next method
    
    # 2. Production: Check config file in proper config directory
    config_dir = get_config_directory()
    
    # Try different config file formats
    config_files = [
        config_dir / "config.toml",
        config_dir / "api_token.txt", 
        config_dir / "token",
    ]
    
    for config_file in config_files:
        if config_file.exists():
            try:
                content = config_file.read_text().strip()
                
                if config_file.name == "config.toml":
                    # Parse simple TOML for api_token
                    for line in content.split('\n'):
                        line = line.strip()
                        if line.startswith('api_token'):
                            parts = line.split('=', 1)
                            if len(parts) == 2:
                                token = parts[1].strip().strip('"\'')
                                if token:
                                    return token
                else:
                    # Plain text token file
                    if content and not content.startswith('#'):
                        return content
            except Exception:
                continue  # Try next file
    
    # 3. Fallback: Environment variable (for CI/CD and development)
    token = os.environ.get("TODOIST_API_TOKEN")
    if token:
        return token
    
    return None

# API Configuration
TODOIST_API_TOKEN = load_api_token()

# Logging Configuration
def setup_logging():
    """Setup logging configuration that works in both development and production."""
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Check if we're in development mode (source directory has main.py)
    current_dir = Path(__file__).parent.parent.parent
    is_development = (current_dir / "main.py").exists()
    
    if is_development:
        # Development mode: log to file in project directory
        log_file = current_dir / "tui.log"
        logging.basicConfig(
            filename=log_file, 
            level=logging.INFO, 
            filemode="w", 
            format=LOG_FORMAT
        )
    else:
        # Production mode: check if logging is explicitly enabled
        enable_file_logging = os.environ.get("TUIDOIST_ENABLE_LOGGING", "false").lower() == "true"
        
        if enable_file_logging:
            # Use user's data directory for log files (following XDG spec)
            if os.name == 'nt':  # Windows
                log_dir = Path.home() / "AppData" / "Local" / "tuidoist"
            else:
                # Unix-like: Use XDG_DATA_HOME or ~/.local/share
                xdg_data_home = os.environ.get('XDG_DATA_HOME')
                if xdg_data_home:
                    log_dir = Path(xdg_data_home) / "tuidoist"
                else:
                    log_dir = Path.home() / ".local" / "share" / "tuidoist"
            
            log_dir.mkdir(parents=True, exist_ok=True)
            log_file = log_dir / "tui.log"
            
            logging.basicConfig(
                filename=log_file,
                level=logging.INFO,
                filemode="w", 
                format=LOG_FORMAT
            )
        else:
            # Disable file logging, only console logging for errors
            logging.basicConfig(
                level=logging.WARNING,
                format=LOG_FORMAT
            )

# Setup logging
setup_logging()

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
