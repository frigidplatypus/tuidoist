# Ptaskwarrior TUI

A modern, modal TUI (Terminal User Interface) for viewing and managing Todoist tasks using [Textual](https://textual.textualize.io/).

## Features

- **Vim-like navigation** with `j`/`k` keys
- **Modal interface** for task operations
- **Project filtering** to focus on specific projects
- **Natural language support** for adding and editing tasks
- **Label display with colors** matching Todoist's official color scheme
- **Quick task operations**: complete, delete, edit, move between projects

## Project Structure

The application has been refactored from a monolithic `tui.py` file into a well-organized package structure:

```
ptaskwarrior_tui/
├── __init__.py          # Package initialization and exports
├── app.py               # Main application class (TodoistTUI)
├── api/                 # Todoist API client wrapper
│   └── __init__.py      # TodoistClient class with caching
├── config/              # Configuration settings
│   └── __init__.py      # API tokens, colors, logging setup
├── screens/             # Modal screens for various operations
│   └── __init__.py      # Add/Edit/Delete/Project selection screens
├── utils/               # Utility functions
│   └── __init__.py      # Label formatting, date parsing, etc.
└── widgets/             # Custom widgets (extensible)
    └── __init__.py      # Placeholder for future custom widgets
```

## Key Bindings

- `q` - Quit the application
- `j` / `k` - Navigate down/up
- `gg` / `G` - Go to top/bottom
- `d` - Complete selected task
- `D` - Delete selected task
- `a` - Add new task (supports natural language)
- `e` - Edit selected task
- `p` - Select project filter
- `P` - Change task's project

## Installation & Setup

1. **Set your Todoist API token**:
   ```bash
   export TODOIST_API_TOKEN="your_token_here"
   ```

2. **Install dependencies**:
   ```bash
   uv sync
   ```

3. **Run the application**:
   ```bash
   python main.py
   # or using the package entry point:
   ptaskwarrior-tui
   ```

## Architecture Benefits

The refactored architecture provides several advantages:

### 🎯 **Separation of Concerns**
- **API logic** isolated in `api/` module with caching
- **UI screens** organized in `screens/` module  
- **Business logic** in the main `app.py`
- **Configuration** centralized in `config/`

### 🔧 **Maintainability**
- Each modal screen is in its own class
- API interactions are centralized and reusable
- Utility functions are testable in isolation
- Clear module boundaries make debugging easier

### 🚀 **Extensibility**
- Easy to add new modal screens
- API client can be extended with new endpoints
- Custom widgets can be added to `widgets/` module
- Configuration can be expanded without touching business logic

### 🧪 **Testability**
- Individual modules can be unit tested
- API client can be mocked for testing UI components
- Utility functions are pure and easily testable

## Development

The codebase follows Python best practices:

- **Type hints** throughout for better IDE support
- **Logging** for debugging and monitoring
- **Error handling** with user-friendly feedback
- **Modular design** for easy maintenance

## Natural Language Support

The app supports Todoist's natural language processing for task creation and editing:

- `"Buy milk tomorrow at 3pm #shopping @urgent"`
- `"Call dentist next Monday"`
- `"Review project proposal by Friday"`

## Label Colors

Labels are displayed with colors matching Todoist's official color scheme, making it easy to visually organize and identify tasks by their labels.

---

*This TUI provides a keyboard-focused, efficient way to manage your Todoist tasks without leaving the terminal.*
