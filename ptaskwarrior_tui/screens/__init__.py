"""Modal screens for the Todoist TUI."""

import logging
from typing import List, Tuple, cast, TYPE_CHECKING, Optional

from textual.widgets import Label, Button, DataTable, Input, OptionList, SelectionList
from textual.widgets.option_list import Option
from textual.widgets.selection_list import Selection
from textual.containers import Vertical, Horizontal
from textual.screen import ModalScreen
from textual.coordinate import Coordinate
from todoist_api_python.models import Project

from ..utils import extract_task_id_from_row_key

if TYPE_CHECKING:
    from ..app import TodoistTUI

logger = logging.getLogger(__name__)


class CustomSelectionList(SelectionList):
    """Custom SelectionList that prevents default enter behavior."""
    
    def key_enter(self, event):
        """Override enter key to prevent default selection behavior."""
        # Prevent the default enter behavior and don't do anything
        # This allows the parent screen to handle the enter key
        event.prevent_default()
        return


class DeleteConfirmScreen(ModalScreen):
    """Modal screen for confirming task deletion."""
    
    def __init__(self, task_id_str: str, row_key):
        super().__init__()
        self.task_id_str = task_id_str  # String version for API
        self.row_key = row_key  # RowKey for table removal

    def compose(self):
        yield Vertical(
            Label("Delete this task? (y/n)"),
            Button("Yes", id="confirm_delete"),
            Button("No", id="cancel_delete")
        )

    def on_button_pressed(self, event):
        app = cast("TodoistTUI", self.app)
        if event.button.id == "confirm_delete":
            table = app.query_one(DataTable)
            if app.client.delete_task(self.task_id_str):
                table.remove_row(self.row_key)  # Remove using the row key
            else:
                app.bell()
            self.dismiss()
        elif event.button.id == "cancel_delete":
            self.dismiss()


class ProjectSelectScreen(ModalScreen):
    """Modal screen for selecting a project to filter by."""
    
    BINDINGS = [
        ("escape", "dismiss", "Cancel"),
        ("q", "dismiss", "Cancel"),
        ("j", "down", "Down"),
        ("k", "up", "Up"),
        ("gg", "top", "Go to Top"),
        ("G", "bottom", "Go to Bottom"),
        ("enter", "select_project", "Select"),
    ]

    def __init__(self, projects: List[Project], active_project_id: Optional[str]):
        super().__init__()
        self.projects = projects
        self.active_project_id = active_project_id

    def compose(self):
        yield Vertical(
            Label("Select Project (j/k to navigate, Enter to select, q to cancel):"),
            DataTable(id="project_table"),
        )

    def on_mount(self) -> None:
        table = self.query_one("#project_table", DataTable)
        table.add_columns("Project Name")
        table.cursor_type = "row"
        
        # Add "All Projects" option
        table.add_row("All Projects", key="all")
        
        # Add individual projects
        for project in self.projects:
            if isinstance(project, Project):
                table.add_row(project.name, key=project.id)
        
        # Set cursor to current active project
        table.cursor_coordinate = Coordinate(0, 0)

    def action_down(self) -> None:
        table = self.query_one("#project_table", DataTable)
        table.action_cursor_down()

    def action_up(self) -> None:
        table = self.query_one("#project_table", DataTable)
        table.action_cursor_up()

    def action_top(self) -> None:
        table = self.query_one("#project_table", DataTable)
        if table.row_count > 0:
            table.cursor_coordinate = Coordinate(0, 0)

    def action_bottom(self) -> None:
        table = self.query_one("#project_table", DataTable)
        if table.row_count > 0:
            table.cursor_coordinate = Coordinate(table.row_count - 1, 0)

    def action_select_project(self) -> None:
        table = self.query_one("#project_table", DataTable)
        row = table.cursor_coordinate.row if table.cursor_coordinate else None
        if row is not None:
            try:
                row_keys = list(table.rows.keys())
                if 0 <= row < len(row_keys):
                    row_key = row_keys[row]
                    app = cast("TodoistTUI", self.app)
                    
                    if row_key == "all":
                        app.set_active_project(None)
                    else:
                        app.set_active_project(str(row_key))
                    
                    self.dismiss()
            except (AttributeError, IndexError):
                pass

    def on_data_table_row_selected(self, event) -> None:
        self.action_select_project()


class ChangeProjectScreen(ModalScreen):
    """Screen for changing a task's project with fuzzy filtering."""

    BINDINGS = [
        ("escape", "dismiss", "Cancel"),
        ("ctrl+c", "dismiss", "Cancel"),
        ("tab", "toggle_focus", "Toggle Focus"),
        ("enter", "select", "Select Project"),
    ]

    def __init__(self, task_id: str, projects: List[Tuple[str, str]]):
        super().__init__()
        self.task_id = task_id
        self.projects = projects  # List of (project_id, project_name) tuples
        self.filtered_projects = projects.copy()

    def compose(self):
        yield Vertical(
            Label("Change task project (type to filter, Tab to switch focus, Escape to cancel):"),
            Input(placeholder="Type to filter projects...", id="project_filter"),
            OptionList(*[Option(name, id=proj_id) for proj_id, name in self.projects], id="project_list"),
            id="change_project_container"
        )

    def on_mount(self):
        # Start with the option list focused so navigation works immediately
        option_list = self.query_one("#project_list", OptionList)
        option_list.focus()
        if len(option_list.options) > 0:
            option_list.highlighted = 0

    def action_toggle_focus(self):
        """Toggle focus between input and option list."""
        input_field = self.query_one("#project_filter", Input)
        option_list = self.query_one("#project_list", OptionList)
        
        if input_field.has_focus:
            option_list.focus()
        else:
            input_field.focus()

    def on_input_changed(self, event):
        """Handle fuzzy filtering as user types."""
        if event.input.id == "project_filter":
            filter_text = event.value.lower()
            if not filter_text:
                # Show all projects if no filter
                filtered_options = [Option(name, id=proj_id) for proj_id, name in self.projects]
            else:
                # Simple fuzzy matching - contains all characters in order
                filtered_projects = []
                for proj_id, name in self.projects:
                    name_lower = name.lower()
                    if all(char in name_lower for char in filter_text):
                        filtered_projects.append((proj_id, name))
                filtered_options = [Option(name, id=proj_id) for proj_id, name in filtered_projects]
            
            option_list = self.query_one("#project_list", OptionList)
            option_list.clear_options()
            for option in filtered_options:
                option_list.add_option(option)
            
            # Auto-highlight first option if any exist
            if filtered_options:
                option_list.highlighted = 0

    def on_key(self, event):
        """Handle key presses when input field doesn't have focus."""
        option_list = self.query_one("#project_list", OptionList)
        input_field = self.query_one("#project_filter", Input)
        
        # If option list has focus, handle vim-like navigation
        if option_list.has_focus:
            if event.key == "j":
                option_list.action_cursor_down()
                event.prevent_default()
            elif event.key == "k":
                option_list.action_cursor_up()
                event.prevent_default()
            elif event.key == "q":
                self.dismiss()
                event.prevent_default()
            elif event.key.isprintable() and len(event.key) == 1:
                # If user types a printable character while option list is focused,
                # switch focus to input and add the character
                input_field.focus()
                input_field.value += event.key
                event.prevent_default()

    def action_down(self):
        option_list = self.query_one("#project_list", OptionList)
        option_list.action_cursor_down()

    def action_up(self):
        option_list = self.query_one("#project_list", OptionList)
        option_list.action_cursor_up()

    def action_top(self):
        option_list = self.query_one("#project_list", OptionList)
        if len(option_list.options) > 0:
            option_list.highlighted = 0

    def action_bottom(self):
        option_list = self.query_one("#project_list", OptionList)
        if len(option_list.options) > 0:
            option_list.highlighted = len(option_list.options) - 1

    def action_select(self):
        option_list = self.query_one("#project_list", OptionList)
        if option_list.highlighted is not None and 0 <= option_list.highlighted < len(option_list.options):
            highlighted_option = option_list.options[option_list.highlighted]
            if highlighted_option:
                self.select_project(highlighted_option.id)

    def on_option_list_option_selected(self, event):
        """Handle project selection from OptionList."""
        if event.option_list.id == "project_list":
            self.select_project(event.option.id)

    def select_project(self, project_id):
        """Move the task to the selected project."""
        app = cast("TodoistTUI", self.app)
        if app.client.move_task(self.task_id, project_id):
            # Refresh the task list
            app.run_worker(app.fetch_tasks, thread=True)
            self.dismiss()
        else:
            app.bell()


class AddTaskScreen(ModalScreen):
    """Screen for adding a new task with natural language support."""

    BINDINGS = [
        ("escape", "dismiss", "Cancel"),
        ("ctrl+c", "dismiss", "Cancel"),
        ("enter", "add_task", "Add Task"),
    ]

    def compose(self):
        yield Vertical(
            Label("Add new task (Enter to add, Escape to cancel):"),
            Label("Natural language supported - e.g., 'Buy milk tomorrow at 3pm #shopping @urgent'"),
            Input(placeholder="Enter task description...", id="task_input"),
            id="add_task_container"
        )

    def on_mount(self):
        # Focus the input field when the modal opens
        input_field = self.query_one("#task_input", Input)
        input_field.focus()

    def on_input_submitted(self, event):
        """Handle Enter key pressed in the input field."""
        if event.input.id == "task_input":
            self.action_add_task()

    def action_add_task(self):
        """Add the task using natural language processing."""
        input_field = self.query_one("#task_input", Input)
        text = input_field.value.strip()
        
        if text:
            self.add_task(text)
        else:
            # Flash to indicate empty input
            app = cast("TodoistTUI", self.app)
            app.bell()

    def add_task(self, text: str):
        """Add a task using Todoist's natural language processing."""
        app = cast("TodoistTUI", self.app)
        
        if app.client.add_task_quick(text):
            # Refresh the task list to show the new task
            app.run_worker(app.fetch_tasks, thread=True)
            self.dismiss()
        else:
            app.bell()


class EditTaskScreen(ModalScreen):
    """Screen for editing an existing task."""

    BINDINGS = [
        ("escape", "dismiss", "Cancel"),
        ("ctrl+c", "dismiss", "Cancel"),
        ("enter", "update_task", "Update Task"),
    ]

    def __init__(self, task_id: str, current_task, client):
        super().__init__()
        self.task_id = task_id
        self.current_task = current_task
        self.client = client
        self.current_content = current_task.content

    def compose(self):
        # Get current task details
        project_name = self.client.get_project_name(self.current_task.project_id)
        due_date = getattr(self.current_task.due, 'date', 'No due date') if self.current_task.due else 'No due date'
        
        # Format current labels
        current_labels = []
        if self.current_task.labels:
            for label_id in self.current_task.labels:
                label_name = self.client.get_label_name(label_id)
                current_labels.append(f"@{label_name}")
        labels_text = ', '.join(current_labels) if current_labels else 'No labels'
        
        yield Vertical(
            Label("Edit task (Enter to update, Escape to cancel):"),
            Label(f"[bold]Current project:[/bold] #{project_name}"),
            Label(f"[bold]Due date:[/bold] {due_date}"),
            Label(f"[bold]Labels:[/bold] {labels_text}"),
            Label(""),
            Label("Natural language supported - e.g., 'Task #ProjectName @label tomorrow'"),
            Input(value=self.current_content, id="task_input"),
            id="edit_task_container"
        )

    def on_mount(self):
        # Focus the input field when the modal opens  
        input_field = self.query_one("#task_input", Input)
        input_field.focus()
        # Move cursor to end of text - this should not auto-select
        self.call_after_refresh(self._position_cursor)

    def _position_cursor(self):
        """Position cursor at end of text after the widget is fully mounted."""
        input_field = self.query_one("#task_input", Input)
        input_field.cursor_position = len(input_field.value)

    def action_update_task(self):
        """Update the task content."""
        input_field = self.query_one("#task_input", Input)
        new_content = input_field.value.strip()
        
        if new_content and new_content != self.current_content:
            self.update_task(new_content)
        elif not new_content:
            # Flash to indicate empty input
            app = cast("TodoistTUI", self.app)
            app.bell()
        else:
            # No changes made, just dismiss
            self.dismiss()

    def on_input_submitted(self, event):
        """Handle Enter key press in the input field."""
        if event.input.id == "task_input":
            self.action_update_task()

    def update_task(self, new_content: str):
        """Update the task using natural language processing where possible."""
        from ..app import TodoistTUI
        app = cast(TodoistTUI, self.app)
        
        # Use natural language processing for the full content
        if self.client.update_task_with_natural_language(self.task_id, new_content):
            # Refresh the task list to show the updated task
            app.run_worker(app.fetch_tasks, thread=True)
            self.dismiss()
        else:
            app.bell()


class LabelManagementScreen(ModalScreen):
    """Modal screen for managing task labels with multi-select functionality."""
    
    BINDINGS = [
        ("escape", "dismiss", "Cancel"),
        ("q", "dismiss", "Cancel"),
        ("j", "down", "Down"),
        ("k", "up", "Up"),
        ("gg", "top", "Go to Top"),
        ("G", "bottom", "Go to Bottom"),
        ("space", "toggle_label", "Toggle Label"),
        ("a", "add_label", "Add Label"),
        ("enter", "apply_changes", "Apply Changes"),
        ("/", "focus_filter", "Filter Labels"),
        ("tab", "toggle_focus", "Toggle Focus"),
    ]
    
    def __init__(self, task_id: str, current_labels: List[str], available_labels: List[Tuple[str, str, str]]):
        """
        Initialize the label management screen.
        
        Args:
            task_id: The ID of the task to manage labels for
            current_labels: List of current label names on the task
            available_labels: List of (label_id, label_name, label_color) tuples
        """
        super().__init__()
        self.task_id = task_id
        self.current_labels = set(current_labels)
        self.available_labels = available_labels
        self.filtered_labels = available_labels.copy()  # Initially show all labels
        self.in_add_mode = False

    def compose(self):
        """Compose the label management interface."""
        # Create selections for the SelectionList
        selections = []
        for label_id, label_name, label_color in self.available_labels:
            # Check if this label is currently selected
            initial_state = label_name in self.current_labels
            # Create a rich text prompt that shows the label with color
            prompt = f"[{label_color}]●[/] {label_name}"
            selections.append(Selection(prompt, label_name, initial_state=initial_state))
        
        yield Vertical(
            Label("Manage Labels", classes="title"),
            Label("/ to filter, j/k to navigate, space to toggle, a to add, enter to apply, q to cancel:"),
            Input(placeholder="Type to filter labels...", id="filter_input"),
            CustomSelectionList(*selections, id="label_list"),
            Input(placeholder="Type new label name and press Enter...", id="new_label_input", classes="hidden"),
            Horizontal(
                Button("Apply", id="apply_labels", variant="primary"),
                Button("Cancel", id="cancel_labels"),
                classes="button_row",
            ),
            classes="label_management",
        )

    def on_mount(self):
        """Focus the SelectionList when the modal opens."""
        self.query_one("#label_list", CustomSelectionList).focus()

    def on_key(self, event):
        """Handle key presses, especially enter when selection list has focus."""
        label_list = self.query_one("#label_list", CustomSelectionList)
        
        if event.key == "enter" and label_list.has_focus:
            # If enter is pressed while selection list has focus, apply changes
            self.action_apply_changes()
            event.prevent_default()
            return
        
        # For other keys, don't prevent default behavior

    def on_input_changed(self, event):
        """Handle filter input changes."""
        if event.input.id == "filter_input":
            self._filter_labels(event.value)

    def _filter_labels(self, filter_text: str):
        """Filter the labels based on the search text."""
        if not filter_text.strip():
            # Show all labels if filter is empty
            self.filtered_labels = self.available_labels.copy()
        else:
            # Filter labels that contain the search text (case-insensitive)
            filter_lower = filter_text.lower()
            self.filtered_labels = [
                (label_id, label_name, label_color)
                for label_id, label_name, label_color in self.available_labels
                if filter_lower in label_name.lower()
            ]
        
        # Update the SelectionList with filtered results
        self._update_selection_list()

    def _update_selection_list(self):
        """Update the SelectionList with current filtered labels."""
        label_list = self.query_one("#label_list", CustomSelectionList)
        
        # Get current selections before clearing
        current_selections = set(label_list.selected) if hasattr(label_list, 'selected') else set()
        
        # Clear and repopulate with filtered labels
        label_list.clear_options()
        
        selections = []
        for label_id, label_name, label_color in self.filtered_labels:
            # Maintain selection state for labels that are still visible
            initial_state = (label_name in self.current_labels or 
                           label_name in current_selections)
            prompt = f"[{label_color}]●[/] {label_name}"
            selections.append(Selection(prompt, label_name, initial_state=initial_state))
        
        if selections:
            label_list.add_options(selections)

    def action_focus_filter(self):
        """Focus the filter input field."""
        if not self.in_add_mode:
            filter_input = self.query_one("#filter_input", Input)
            filter_input.focus()

    def action_toggle_focus(self):
        """Toggle focus between filter input and selection list."""
        filter_input = self.query_one("#filter_input", Input)
        label_list = self.query_one("#label_list", CustomSelectionList)
        
        if filter_input.has_focus:
            label_list.focus()
        else:
            filter_input.focus()

    def action_down(self):
        """Move down in the list."""
        if not self.in_add_mode:
            label_list = self.query_one("#label_list", CustomSelectionList)
            if label_list.has_focus:
                label_list.action_cursor_down()

    def action_up(self):
        """Move up in the list."""
        if not self.in_add_mode:
            label_list = self.query_one("#label_list", CustomSelectionList)
            if label_list.has_focus:
                label_list.action_cursor_up()

    def action_top(self):
        """Go to top of the list."""
        if not self.in_add_mode:
            label_list = self.query_one("#label_list", CustomSelectionList)
            if label_list.has_focus:
                label_list.action_first()

    def action_bottom(self):
        """Go to bottom of the list."""
        if not self.in_add_mode:
            label_list = self.query_one("#label_list", CustomSelectionList)
            if label_list.has_focus:
                label_list.action_last()

    def action_toggle_label(self):
        """Toggle the currently highlighted label."""
        if not self.in_add_mode:
            label_list = self.query_one("#label_list", CustomSelectionList)
            if label_list.has_focus:
                label_list.action_select()

    def action_add_label(self):
        """Enter add label mode."""
        self.in_add_mode = True
        input_widget = self.query_one("#new_label_input", Input)
        input_widget.remove_class("hidden")
        input_widget.focus()
        input_widget.value = ""

    def action_apply_changes(self):
        """Apply the label changes to the task."""
        if self.in_add_mode:
            # If in add mode, treat enter as submitting the new label
            self._submit_new_label()
        else:
            # Otherwise, apply the changes
            self._apply_label_changes()

    def on_button_pressed(self, event):
        """Handle button presses."""
        if event.button.id == "apply_labels":
            self._apply_label_changes()
        elif event.button.id == "cancel_labels":
            self.dismiss()

    def on_input_submitted(self, event):
        """Handle input submission (Enter key)."""
        if event.input.id == "new_label_input":
            self._submit_new_label()
        elif event.input.id == "filter_input":
            # If enter is pressed in filter, focus the label list
            self.query_one("#label_list", CustomSelectionList).focus()

    def _submit_new_label(self):
        """Submit a new label."""
        input_widget = self.query_one("#new_label_input", Input)
        new_label_name = input_widget.value.strip()
        
        if new_label_name:
            app = cast("TodoistTUI", self.app)
            # Try to create the new label
            if app.client.create_label(new_label_name):
                # Refresh the available labels and recreate the SelectionList
                app.client.fetch_labels()  # Refresh cache
                self._refresh_available_labels()
                input_widget.value = ""  # Clear input
            else:
                app.bell()  # Error feedback
        
        # Exit add mode
        self.in_add_mode = False
        input_widget.add_class("hidden")
        self.query_one("#label_list", CustomSelectionList).focus()

    def _apply_label_changes(self):
        """Apply the label changes to the task."""
        app = cast("TodoistTUI", self.app)
        
        # Get selected labels from the SelectionList
        label_list = self.query_one("#label_list", CustomSelectionList)
        selected_labels = list(label_list.selected)
        
        # Update the task with the new labels
        if app.client.update_task_labels(self.task_id, selected_labels):
            app.bell()  # Success feedback
            app._refresh_table_display()  # Refresh the main display
        else:
            app.bell()  # Error feedback
        
        self.dismiss()

    def _refresh_available_labels(self):
        """Refresh the available labels list from the client."""
        app = cast("TodoistTUI", self.app)
        
        # Get updated available labels
        self.available_labels = [
            (label_id, app.client.get_label_name(label_id), app.client.get_label_color(label_id) or "white")
            for label_id in app.client.label_name_map.keys()
        ]
        
        # Re-apply current filter
        filter_input = self.query_one("#filter_input", Input)
        self._filter_labels(filter_input.value)
