# Minimal starter for a modal TUI app using Textual
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, DataTable, Button, Label, OptionList, Input
from textual.widgets.option_list import Option
from textual.containers import Vertical, Horizontal
from textual.screen import ModalScreen
from textual.coordinate import Coordinate
from todoist_api_python.api import TodoistAPI
from todoist_api_python.models import Task, Project
from todoist_api_python.models import Label as TodoistLabel
import os
import logging

logging.basicConfig(filename="tui.log", level=logging.INFO, filemode="w")

TODOIST_API_TOKEN = os.environ.get("TODOIST_API_TOKEN")

class TodoistTUI(App):
    """A Textual TUI for Todoist tasks."""

    TITLE = "Todoist TUI"
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("j", "down", "Down"),
        ("k", "up", "Up"),
        ("gg", "top", "Go to Top"),
        ("G", "bottom", "Go to Bottom"),
        ("d", "complete_task", "Complete Task"),
        ("D", "delete_task", "Delete Task"),
        ("a", "add_task", "Add Task"),
        ("e", "edit_task", "Edit Task"),
        ("p", "select_project", "Select Project"),
        ("P", "change_task_project", "Change Project"),
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.api = TodoistAPI(TODOIST_API_TOKEN) if TODOIST_API_TOKEN and isinstance(TODOIST_API_TOKEN, str) else None
        self.project_name_map = {}  # Maps project ID to project name
        self.label_name_map = {}  # Maps label ID to label name
        self.label_color_map = {}  # Maps label ID to label color
        self.label_by_name = {}  # Maps label name to label name (for reverse lookup)
        self.projects_cache = []  # Store the latest fetched projects
        self.labels_cache = []  # Store the latest fetched labels
        self.tasks_cache = []  # Store the latest fetched tasks
        self.active_project_id = None  # None means show all projects
        self.error = None

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        yield DataTable(id="tasks_table")
        yield Footer()

    def on_mount(self) -> None:
        """Called when app starts."""
        table = self.query_one(DataTable)
        table.add_columns("Task", "Due Date", "Project", "Labels")
        if not TODOIST_API_TOKEN or not isinstance(TODOIST_API_TOKEN, str):
            table.add_row("[bold red]Error: TODOIST_API_TOKEN not set.[/bold red]", "", "", "")
            return
        self.run_worker(self.fetch_tasks, thread=True)

    def get_active_project_name(self) -> str:
        """Get the name of the currently active project."""
        if self.active_project_id is None:
            return "All Projects"
        return self.project_name_map.get(self.active_project_id, "Unknown Project")

    def fetch_tasks(self) -> None:
        """Fetch tasks from the Todoist API."""
        try:
            logging.info("Fetching tasks...")
            if not self.api:
                raise Exception("Todoist API not initialized")
            
            # Fetch projects first to get project names
            projects = list(self.api.get_projects())
            # Handle potentially nested list from the API response
            if projects and isinstance(projects[0], list):
                projects_to_process = projects[0]
            else:
                projects_to_process = projects
            self.project_name_map = {}
            for project in projects_to_process:
                if isinstance(project, Project):
                    self.project_name_map[project.id] = project.name
            self.projects_cache = projects_to_process
            logging.info(f"Fetched {len(projects_to_process)} projects")
            
            # Fetch labels to get label names
            labels = list(self.api.get_labels())
            # Handle potentially nested list from the API response
            if labels and isinstance(labels[0], list):
                labels_to_process = labels[0]
            else:
                labels_to_process = labels
            self.label_name_map = {}
            self.label_by_name = {}
            for label in labels_to_process:
                if isinstance(label, TodoistLabel):
                    self.label_name_map[label.id] = label.name
                    self.label_color_map[label.id] = label.color
                    self.label_by_name[label.name] = label.name  # Name to name mapping
                    logging.info(f"Loaded label: {label.name} (ID: {label.id}) -> color: {label.color}")
            self.labels_cache = labels_to_process
            logging.info(f"Fetched {len(labels_to_process)} labels")
            
            tasks = list(self.api.get_tasks())  # Convert Paginator to a list
            logging.info(f"API returned: {tasks}")  # Log the raw API response
            self.call_from_thread(self.update_table, tasks)
        except Exception as e:
            logging.error(f"An error occurred during fetch: {e}", exc_info=True)
            self.call_from_thread(self.update_table_error, e)

    def update_table(self, tasks: list) -> None:
        """Update the DataTable with tasks."""
        # Handle potentially nested list from the API response
        if tasks and isinstance(tasks[0], list):
            tasks_to_process = tasks[0]
        else:
            tasks_to_process = tasks

        logging.info(f"Updating table with {len(tasks_to_process)} items.")
        self.tasks_cache = tasks_to_process
        self._refresh_table_display()

    def _refresh_table_display(self) -> None:
        """Refresh the table display with current filter settings."""
        table = self.query_one(DataTable)
        table.clear()
        
        # Filter tasks based on active project
        if self.active_project_id is None:
            tasks_to_show = self.tasks_cache
        else:
            tasks_to_show = [task for task in self.tasks_cache if isinstance(task, Task) and task.project_id == self.active_project_id]
        
        if not tasks_to_show:
            if self.active_project_id is None:
                table.add_row("No tasks found.", "", "", "")
            else:
                project_name = self.get_active_project_name()
                table.add_row(f"No tasks found in {project_name}.", "", "", "")
        else:
            for task in tasks_to_show:
                if isinstance(task, Task):
                    due_date = getattr(task.due, 'date', 'N/A')
                    project_name = self.project_name_map.get(task.project_id, 'Unknown Project')
                    # Format labels for display with colors
                    label_names = []
                    if task.labels:  # Check if labels exist and are not None
                        for label_id in task.labels:
                            formatted_label = self.format_label_with_color(label_id)
                            label_names.append(formatted_label)
                    labels_display = ', '.join(label_names) if label_names else ''
                    # Use task.id as the row key (internal identifier)
                    table.add_row(task.content, due_date, project_name, labels_display, key=task.id)
                else:
                    logging.warning(f"Skipping non-task item: {task}")
        
        # Set cursor to first row if any
        if tasks_to_show:
            table.cursor_type = "row"
            from textual.coordinate import Coordinate
            table.cursor_coordinate = Coordinate(0, 0)
        
        # Update the title to show active project
        self.title = f"Todoist TUI - {self.get_active_project_name()}"

    def update_table_error(self, error: Exception) -> None:
        """Update the DataTable with an error message."""
        table = self.query_one(DataTable)
        table.add_row(f"[bold red]Error fetching tasks: {error}[/bold red]", "", "", "")

    def action_down(self) -> None:
        table = self.query_one(DataTable)
        table.action_cursor_down()

    def action_up(self) -> None:
        table = self.query_one(DataTable)
        table.action_cursor_up()

    def action_top(self) -> None:
        table = self.query_one(DataTable)
        if table.row_count > 0:
            from textual.coordinate import Coordinate
            table.cursor_coordinate = Coordinate(0, 0)

    def action_bottom(self) -> None:
        table = self.query_one(DataTable)
        if table.row_count > 0:
            from textual.coordinate import Coordinate
            table.cursor_coordinate = Coordinate(table.row_count - 1, 0)

    def get_selected_row_key(self):
        table = self.query_one(DataTable)
        row = table.cursor_coordinate.row if table.cursor_coordinate else None
        if row is not None:
            # Get the row key directly from the table's internal row keys
            try:
                row_keys = list(table.rows.keys())
                if 0 <= row < len(row_keys):
                    return row_keys[row]  # This will be the task ID
            except (AttributeError, IndexError):
                pass
        return None

    def action_complete_task(self) -> None:
        table = self.query_one(DataTable)
        task_id = self.get_selected_row_key()
        if task_id is not None and self.api:
            try:
                # Extract the actual task ID from the RowKey object
                actual_task_id = task_id.value if hasattr(task_id, 'value') and task_id.value is not None else str(task_id)
                if actual_task_id:
                    self.api.complete_task(actual_task_id)
                    table.remove_row(task_id)  # Remove using the task ID row key
            except Exception as e:
                self.bell()
                logging.error(f"Failed to complete task: {e}")
        else:
            self.bell()

    def action_delete_task(self) -> None:
        task_id = self.get_selected_row_key()
        if task_id is not None:
            # Extract the actual task ID from the RowKey object
            actual_task_id = task_id.value if hasattr(task_id, 'value') and task_id.value is not None else str(task_id)
            if actual_task_id:
                self.push_screen(DeleteConfirmScreen(actual_task_id, task_id))

    def action_select_project(self) -> None:
        """Show project selection modal."""
        if self.projects_cache:
            self.push_screen(ProjectSelectScreen(self.projects_cache, self.active_project_id))

    def set_active_project(self, project_id: str | None = None) -> None:
        """Set the active project and refresh the display."""
        self.active_project_id = project_id
        self._refresh_table_display()

    def action_add_task(self) -> None:
        """Show the add task modal."""
        self.push_screen(AddTaskScreen())

    def action_change_task_project(self) -> None:
        task_id = self.get_selected_row_key()
        if task_id is not None:
            # Extract the actual task ID from the RowKey object
            actual_task_id = task_id.value if hasattr(task_id, 'value') and task_id.value is not None else str(task_id)
            if actual_task_id:
                self.push_screen(ChangeProjectScreen(actual_task_id, list(self.project_name_map.items())))

    def action_edit_task(self) -> None:
        """Show the edit task modal for the selected task."""
        task_id = self.get_selected_row_key()
        if task_id is not None:
            # Extract the actual task ID from the RowKey object
            actual_task_id = task_id.value if hasattr(task_id, 'value') and task_id.value is not None else str(task_id)
            if actual_task_id:
                # Find the task in the cache to get current content
                current_task = None
                for task in self.tasks_cache:
                    if isinstance(task, Task) and task.id == actual_task_id:
                        current_task = task
                        break
                
                if current_task:
                    self.push_screen(EditTaskScreen(actual_task_id, current_task.content))
                else:
                    self.bell()
                    logging.error(f"Could not find task with ID: {actual_task_id}")

    def format_label_with_color(self, label_identifier: str) -> str:
        """Format a label with its color using rich markup."""
        # Try to get the label name (works for both ID and name lookups)
        label_name = self.label_name_map.get(label_identifier) or self.label_by_name.get(label_identifier, label_identifier)
        
        # Try to get the color - first by ID, then by looking up the ID from name
        label_color = None
        if label_identifier in self.label_color_map:
            label_color = self.label_color_map[label_identifier]
        else:
            # Find the label ID by name to get its color
            for label_id, name in self.label_name_map.items():
                if name == label_identifier:
                    label_color = self.label_color_map.get(label_id)
                    break
        
        # Debug logging
        logging.info(f"Label '{label_identifier}' -> name: '{label_name}', color: '{label_color}'")
        
        # Map Todoist colors to rich colors based on official API documentation
        # These are all the official Todoist color names from the API documentation
        color_map = {
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
        
        if label_color and label_color in color_map:
            rich_color = color_map[label_color]
            formatted = f"[{rich_color}]{label_name}[/{rich_color}]"
            logging.info(f"Formatted label: '{formatted}'")
            return formatted
        else:
            logging.info(f"No color mapping found for '{label_color}', returning plain: '{label_name}'")
            return label_name

class DeleteConfirmScreen(ModalScreen):
    def __init__(self, task_id_str, row_key):
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
        from typing import cast
        app = cast(TodoistTUI, self.app)
        if event.button.id == "confirm_delete":
            table = app.query_one(DataTable)
            if app.api:
                try:
                    app.api.delete_task(self.task_id_str)
                except Exception as e:
                    app.bell()
                    logging.error(f"Failed to delete task: {e}")
            table.remove_row(self.row_key)  # Remove using the row key
            self.dismiss()
        elif event.button.id == "cancel_delete":
            self.dismiss()


class ProjectSelectScreen(ModalScreen):
    BINDINGS = [
        ("escape", "dismiss", "Cancel"),
        ("q", "dismiss", "Cancel"),
        ("j", "down", "Down"),
        ("k", "up", "Up"),
        ("gg", "top", "Go to Top"),
        ("G", "bottom", "Go to Bottom"),
        ("enter", "select_project", "Select"),
    ]

    def __init__(self, projects, active_project_id):
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
        from textual.coordinate import Coordinate
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
                    from typing import cast
                    app = cast(TodoistTUI, self.app)
                    
                    if row_key == "all":
                        app.set_active_project(None)
                    else:
                        app.set_active_project(str(row_key))
                    
                    self.dismiss()
            except (AttributeError, IndexError):
                pass

    def on_data_table_row_selected(self, event) -> None:
        self.action_select_project()

    def on_button_pressed(self, event):
        if event.button.id == "cancel_project_select":
            self.dismiss()


class ChangeProjectScreen(ModalScreen):
    """Screen for changing a task's project with fuzzy filtering."""

    BINDINGS = [
        ("escape", "dismiss", "Cancel"),
        ("ctrl+c", "dismiss", "Cancel"),
        ("tab", "toggle_focus", "Toggle Focus"),
        ("enter", "select", "Select Project"),
    ]

    def __init__(self, task_id: str, projects: list):
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
        from typing import cast
        app = cast(TodoistTUI, self.app)
        if app.api:
            try:
                # Use move_task to change the project
                app.api.move_task(task_id=self.task_id, project_id=project_id)
                # Refresh the task list
                app.run_worker(app.fetch_tasks, thread=True)
                self.dismiss()
            except Exception as e:
                app.bell()
                logging.error(f"Failed to change task project: {e}")
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
            from typing import cast
            app = cast(TodoistTUI, self.app)
            app.bell()

    def add_task(self, text: str):
        """Add a task using Todoist's natural language processing."""
        from typing import cast
        app = cast(TodoistTUI, self.app)
        
        if app.api:
            try:
                # Use add_task_quick for natural language processing
                # This will automatically parse dates, projects, labels, etc.
                new_task = app.api.add_task_quick(text=text)
                logging.info(f"Added task: {new_task.content} (ID: {new_task.id})")
                
                # Refresh the task list to show the new task
                app.run_worker(app.fetch_tasks, thread=True)
                self.dismiss()
            except Exception as e:
                app.bell()
                logging.error(f"Failed to add task: {e}")
        else:
            app.bell()
            logging.error("API not initialized")

class EditTaskScreen(ModalScreen):
    """Screen for editing an existing task."""

    BINDINGS = [
        ("escape", "dismiss", "Cancel"),
        ("ctrl+c", "dismiss", "Cancel"),
        ("enter", "update_task", "Update Task"),
    ]

    def __init__(self, task_id: str, current_content: str):
        super().__init__()
        self.task_id = task_id
        self.current_content = current_content

    def compose(self):
        yield Vertical(
            Label("Edit task (Enter to update, Escape to cancel):"),
            Label("Natural language supported - e.g., 'Buy milk tomorrow at 3pm #shopping @urgent'"),
            Input(value=self.current_content, id="task_input"),
            id="edit_task_container"
        )

    def on_mount(self):
        # Focus the input field when the modal opens
        input_field = self.query_one("#task_input", Input)
        input_field.focus()
        # Move cursor to end of text
        input_field.cursor_position = len(input_field.value)

    def action_update_task(self):
        """Update the task content."""
        input_field = self.query_one("#task_input", Input)
        new_content = input_field.value.strip()
        
        if new_content and new_content != self.current_content:
            self.update_task(new_content)
        elif not new_content:
            # Flash to indicate empty input
            from typing import cast
            app = cast(TodoistTUI, self.app)
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
        from typing import cast
        app = cast(TodoistTUI, self.app)
        
        if app.api:
            try:
                # For natural language support, we'll use a hybrid approach:
                # 1. Try to parse the content for natural language elements
                # 2. Use update_task with extracted components
                
                # Simple approach: if the content contains certain keywords,
                # try to extract them for the due_string parameter
                content = new_content.strip()
                due_string = None
                
                # Look for natural language date patterns
                import re
                date_patterns = [
                    r'\b(today|tomorrow|yesterday)\b',
                    r'\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b',
                    r'\b\d{1,2}[/-]\d{1,2}([/-]\d{2,4})?\b',
                    r'\bat \d{1,2}:\d{2}( ?[ap]m)?\b',
                    r'\b(next|this) (week|month|year)\b',
                    r'\bin \d+ (day|week|month|year)s?\b'
                ]
                
                # Check if content contains date-like patterns
                has_date = any(re.search(pattern, content, re.IGNORECASE) for pattern in date_patterns)
                
                if has_date:
                    # Extract potential due date string from the end or specific patterns
                    # This is a simplified approach - in a full implementation,
                    # you might want more sophisticated parsing
                    due_match = re.search(r'\b(due|by|on|at|tomorrow|today|next \w+|this \w+|\d{1,2}[/-]\d{1,2}|\w+day)\b.*$', content, re.IGNORECASE)
                    if due_match:
                        due_string = due_match.group(0)
                        # Remove the due date part from content to get clean task name
                        content = content[:due_match.start()].strip()
                
                # Update the task with extracted components
                updated_task = app.api.update_task(
                    task_id=self.task_id,
                    content=content,
                    due_string=due_string if due_string else None
                )
                
                logging.info(f"Updated task: {updated_task.content} (ID: {updated_task.id})")
                
                # Refresh the task list to show the updated task
                app.run_worker(app.fetch_tasks, thread=True)
                self.dismiss()
            except Exception as e:
                app.bell()
                logging.error(f"Failed to update task: {e}")
        else:
            app.bell()
            logging.error("API not initialized")

if __name__ == "__main__":
    app = TodoistTUI()
    app.run()
