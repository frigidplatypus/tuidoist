# Tuidoist

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
tuidoist/
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
   tuidoist
   ```

## Todoist API Integration

This application integrates with the **Todoist API v1**. For any development work involving the Todoist API, always refer to the canonical, up-to-date documentation:

**📚 [Todoist API v1 Documentation](https://developer.todoist.com/api/v1/)**

### Key API Information
- **Base URL**: `https://api.todoist.com/rest/v1/`
- **Authentication**: Bearer token via `Authorization` header
- **Resources**: Tasks, Projects, Labels, Filters, Comments, and more

### Important Notes
- **Always use the current API v1** - deprecated endpoints (like the sync API) may return 410 Gone errors
- **Check the official documentation** for the latest endpoint specifications, request/response formats, and rate limits
- **API Token**: Get your personal API token from [Todoist Integrations Settings](https://todoist.com/prefs/integrations)

The application's API client is located in `tuidoist/api/` and handles authentication, caching, and error handling for all Todoist API interactions.

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

### ✨ **Adding Tasks** (Full Natural Language)
- `"Buy milk tomorrow at 3pm #shopping @urgent"`
- `"Call dentist next Monday"`  
- `"Review project proposal by Friday"`

### ✨ **Editing Tasks** (Enhanced Natural Language)
When editing tasks, you can now use natural language elements:

- **Projects**: Add `#ProjectName` to move task to that project
  - `"Fix bug #Work"` → moves task to Work project
- **Labels**: Add `@LabelName` to add labels to the task
  - `"Buy groceries @shopping @urgent"` → adds shopping and urgent labels
- **Due Dates**: Add natural language dates
  - `"Complete report tomorrow"` → sets due date to tomorrow
  - `"Meeting next Friday at 2pm"` → sets due date and time

### 📋 **Enhanced Edit Screen**
The edit screen (press `e` on any task) now displays:

- **Current project**: Shows `#ProjectName` of the task
- **Due date**: Shows current due date or "No due date"
- **Current labels**: Shows all current labels as `@label1, @label2`
- **Smart cursor**: Cursor positioned at end of text (no auto-selection)

This context helps you understand the task's current state and makes it easy to append changes using natural language.

### 🔧 **How It Works**
- The app parses `#Project`, `@Label`, and date patterns from your edit
- Automatically moves tasks to the specified project
- Adds the specified labels (creates them if they don't exist)
- Sets due dates using natural language
- Cleans up the task content by removing the parsed elements

## Label Colors

Labels are displayed with colors matching Todoist's official color scheme, making it easy to visually organize and identify tasks by their labels.

---

*This TUI provides a keyboard-focused, efficient way to manage your Todoist tasks without leaving the terminal.*
