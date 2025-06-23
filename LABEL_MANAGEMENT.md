# Label Management Feature Implementation

## Overview
Added a comprehensive label management modal screen to the Todoist TUI that allows users to:
- View all available labels with colors
- Toggle label selection for the current task
- Add new labels on-the-fly
- Navigate using consistent keybindings

## Key Features

### Navigation Keybindings (consistent with main app)
- `j` / `k` - Navigate down/up in the label list
- `gg` - Go to top of list
- `G` - Go to bottom of list
- `space` - Toggle selected label on/off
- `a` - Add new label (enters add mode)
- `enter` - Apply changes to task
- `q` / `escape` - Cancel and close modal

### Label Management Workflow
1. Select a task in the main view
2. Press `l` to open the label management modal
3. Navigate with `j`/`k` and toggle labels with `space`
4. Press `a` to add a new label:
   - Input field appears
   - Type label name and press `enter`
   - New label is created and added to the list
   - Returns to selection mode
5. Press `enter` to apply all changes
6. Press `q` to cancel without saving

### Visual Features
- Labels display with colored dots (●) matching their Todoist colors
- Currently selected labels are pre-checked
- Clean modal interface with consistent styling
- Hidden input field that appears only in add mode

## Implementation Details

### Files Modified/Created
1. `tuidoist/screens/__init__.py` - Added `LabelManagementScreen` class
2. `tuidoist/api/__init__.py` - Added `update_task_labels()` and `create_label()` methods
3. `tuidoist/app.py` - Added `l` keybinding and `action_manage_labels()` method
4. `tuidoist/styles.tcss` - Added CSS styling for the modal

### Key Methods
- `LabelManagementScreen.compose()` - Creates the UI with SelectionList widget
- `LabelManagementScreen.action_add_label()` - Handles 'a' key to add new labels
- `LabelManagementScreen.action_apply_changes()` - Applies changes on 'enter'
- `TodoistClient.update_task_labels()` - Updates task labels via API
- `TodoistClient.create_label()` - Creates new labels via API

### SelectionList Integration
- Uses Textual's `SelectionList` widget for multi-select functionality
- Supports initial state based on current task labels
- Rich text prompts with colored label indicators
- Maintains selection state during label additions

## Usage Example
1. Run the app: `python -m tuidoist.app`
2. Select any task with `j`/`k`
3. Press `l` to open label management
4. Navigate with `j`/`k`, toggle with `space`
5. Press `a` to add "urgent" label
6. Type "urgent" and press `enter`
7. Press `enter` to apply all changes

## Benefits
- Consistent navigation experience with the main app
- Intuitive multi-select interface
- Ability to create labels without leaving the modal
- Visual feedback with colored label indicators
- Follows Textual best practices for modal screens
