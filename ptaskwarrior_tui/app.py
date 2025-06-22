"""Main application module fo    BINDINGS = [
        ("q", "quit", "Quit"),
        ("j", "down", "Down"),
        ("k", "up", "Up"),
        ("gg", "top", "Top"),
        ("G", "bottom", "Bottom"),
        ("r", "refresh", "Refresh"),
        ("d", "complete_task", "Complete"),
        ("D", "delete_task", "Delete"),
        ("a", "add_task", "Add"),
        ("e", "edit_task", "Edit"),
        ("p", "select_project", "Project"),
        ("P", "change_task_project", "Move"),
        ("l", "manage_labels", "Labels"),
    ]TUI."""

import logging
from typing import Optional, List, cast
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, DataTable
from textual.coordinate import Coordinate
from todoist_api_python.models import Task

from .api import TodoistClient
from .config import TODOIST_API_TOKEN
from .utils import format_label_with_color, extract_task_id_from_row_key
from .screens import (
    DeleteConfirmScreen,
    ProjectSelectScreen,
    ChangeProjectScreen,
    AddTaskScreen,
    EditTaskScreen,
    LabelManagementScreen,
)

logger = logging.getLogger(__name__)


class TodoistTUI(App):
    """A Textual TUI for Todoist tasks."""

    TITLE = "Todoist TUI"
    CSS_PATH = "styles.tcss"
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("j", "down", ""),  # Hidden from footer but still functional
        ("k", "up", ""),    # Hidden from footer but still functional
        ("gg", "top", ""),  # Hidden from footer but still functional
        ("G", "bottom", ""), # Hidden from footer but still functional
        ("r", "refresh", "Refresh"),
        ("d", "complete_task", "Complete"),
        ("D", "delete_task", "Delete"),
        ("a", "add_task", "Add"),
        ("e", "edit_task", "Edit"),
        ("p", "select_project", "Project"),
        ("P", "change_task_project", "Move"),
        ("l", "manage_labels", "Labels"),
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.client = TodoistClient()
        self.active_project_id: Optional[str] = None  # None means show all projects
        self.error: Optional[str] = None

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        yield DataTable(id="tasks_table")
        yield Footer()

    def on_mount(self) -> None:
        """Called when app starts."""
        table = self.query_one(DataTable)
        table.add_columns("Task", "Due Date", "Project", "Labels")
        
        if not self.client.is_initialized:
            table.add_row("[bold red]Error: TODOIST_API_TOKEN not set.[/bold red]", "", "", "")
            return
        
        self.run_worker(self.fetch_tasks, thread=True)

    def get_active_project_name(self) -> str:
        """Get the name of the currently active project."""
        if self.active_project_id is None:
            return "All Projects"
        return self.client.get_project_name(self.active_project_id)

    def fetch_tasks(self) -> None:
        """Fetch tasks from the Todoist API."""
        try:
            logger.info("Fetching tasks...")
            
            # Fetch projects first to get project names
            self.client.fetch_projects()
            
            # Fetch labels to get label names and colors
            self.client.fetch_labels()
            
            # Fetch tasks
            tasks = self.client.fetch_tasks()
            self.call_from_thread(self.update_table, tasks)
        except Exception as e:
            logger.error(f"An error occurred during fetch: {e}", exc_info=True)
            self.call_from_thread(self.update_table_error, e)

    def update_table(self, tasks: List[Task]) -> None:
        """Update the DataTable with tasks."""
        logger.info(f"Updating table with {len(tasks)} items.")
        self._refresh_table_display()

    def _refresh_table_display(self) -> None:
        """Refresh the table display with current filter settings."""
        table = self.query_one(DataTable)
        table.clear()
        
        # Filter tasks based on active project
        if self.active_project_id is None:
            tasks_to_show = self.client.tasks_cache
        else:
            tasks_to_show = [
                task for task in self.client.tasks_cache 
                if isinstance(task, Task) and task.project_id == self.active_project_id
            ]
        
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
                    project_name = self.client.get_project_name(task.project_id)
                    
                    # Format labels for display with colors
                    label_names = []
                    if task.labels:  # Check if labels exist and are not None
                        for label_id in task.labels:
                            formatted_label = format_label_with_color(
                                label_id,
                                self.client.label_name_map,
                                self.client.label_color_map,
                                self.client.label_by_name
                            )
                            label_names.append(formatted_label)
                    labels_display = ', '.join(label_names) if label_names else ''
                    
                    # Use task.id as the row key (internal identifier)
                    table.add_row(task.content, due_date, project_name, labels_display, key=task.id)
                else:
                    logger.warning(f"Skipping non-task item: {task}")
        
        # Set cursor to first row if any
        if tasks_to_show:
            table.cursor_type = "row"
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
            table.cursor_coordinate = Coordinate(0, 0)

    def action_bottom(self) -> None:
        table = self.query_one(DataTable)
        if table.row_count > 0:
            table.cursor_coordinate = Coordinate(table.row_count - 1, 0)

    def action_refresh(self) -> None:
        """Refresh tasks from the server and update the display."""
        # Fetch fresh data from the server
        self.client.fetch_tasks()
        self.client.fetch_projects() 
        self.client.fetch_labels()
        
        # Refresh the table display
        self._refresh_table_display()
        
        # Provide user feedback with visual notification
        self.notify("Tasks refreshed!", severity="information")

    def get_selected_row_key(self):
        """Get the row key of the currently selected row."""
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
        """Complete the currently selected task."""
        table = self.query_one(DataTable)
        task_id = self.get_selected_row_key()
        if task_id is not None:
            actual_task_id = extract_task_id_from_row_key(task_id)
            if actual_task_id and self.client.complete_task(actual_task_id):
                table.remove_row(task_id)  # Remove using the task ID row key
            else:
                self.bell()
        else:
            self.bell()

    def action_delete_task(self) -> None:
        """Show delete confirmation for the currently selected task."""
        task_id = self.get_selected_row_key()
        if task_id is not None:
            actual_task_id = extract_task_id_from_row_key(task_id)
            if actual_task_id:
                self.push_screen(DeleteConfirmScreen(actual_task_id, task_id))

    def action_select_project(self) -> None:
        """Show project selection modal."""
        if self.client.projects_cache:
            self.push_screen(ProjectSelectScreen(self.client.projects_cache, self.active_project_id))

    def set_active_project(self, project_id: Optional[str] = None) -> None:
        """Set the active project and refresh the display."""
        self.active_project_id = project_id
        self._refresh_table_display()

    def action_add_task(self) -> None:
        """Show the add task modal."""
        self.push_screen(AddTaskScreen())

    def action_change_task_project(self) -> None:
        """Show the change project modal for the currently selected task."""
        task_id = self.get_selected_row_key()
        if task_id is not None:
            actual_task_id = extract_task_id_from_row_key(task_id)
            if actual_task_id:
                self.push_screen(ChangeProjectScreen(
                    actual_task_id, 
                    list(self.client.project_name_map.items())
                ))

    def action_edit_task(self) -> None:
        """Show the edit task modal for the selected task."""
        task_id = self.get_selected_row_key()
        if task_id is not None:
            actual_task_id = extract_task_id_from_row_key(task_id)
            if actual_task_id:
                # Find the task in the cache to get current content
                current_task = None
                for task in self.client.tasks_cache:
                    if isinstance(task, Task) and task.id == actual_task_id:
                        current_task = task
                        break
                
                if current_task:
                    self.push_screen(EditTaskScreen(actual_task_id, current_task, self.client))
                else:
                    self.bell()
                    logger.error(f"Could not find task with ID: {actual_task_id}")

    def action_manage_labels(self) -> None:
        """Show the label management modal for the selected task."""
        task_id = self.get_selected_row_key()
        if task_id is not None:
            actual_task_id = extract_task_id_from_row_key(task_id)
            if actual_task_id:
                # Find the task in the cache to get current labels
                current_task = None
                for task in self.client.tasks_cache:
                    if isinstance(task, Task) and task.id == actual_task_id:
                        current_task = task
                        break
                
                if current_task:
                    # Get current label names
                    current_labels = [self.client.get_label_name(label_id) for label_id in current_task.labels or []]
                    
                    # Get available labels (label_id, label_name, label_color)
                    available_labels = [
                        (label_id, self.client.get_label_name(label_id), self.client.get_label_color(label_id) or "white")
                        for label_id in self.client.label_name_map.keys()
                    ]
                    
                    self.push_screen(LabelManagementScreen(actual_task_id, current_labels, available_labels))
                else:
                    self.bell()
                    logger.error(f"Could not find task with ID: {actual_task_id}")


def main():
    """Entry point for the application."""
    app = TodoistTUI()
    app.run()


if __name__ == "__main__":
    main()
