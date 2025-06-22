"""Modal screens for the Todoist TUI."""

import logging
from typing import List, Tuple, cast, TYPE_CHECKING, Optional

from textual.widgets import Label, Button, DataTable, Input, OptionList
from textual.widgets.option_list import Option
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.coordinate import Coordinate
from todoist_api_python.models import Project

from ..utils import extract_task_id_from_row_key

if TYPE_CHECKING:
    from ..app import TodoistTUI

logger = logging.getLogger(__name__)


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
