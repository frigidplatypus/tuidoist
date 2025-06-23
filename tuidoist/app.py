"""Main application module for the Todoist TUI.

This application integrates with the Todoist REST API v1.
Canonical API documentation: https://developer.todoist.com/api/v1/
"""

import logging
from typing import Optional, List, Any
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, DataTable
from textual.coordinate import Coordinate
from todoist_api_python.models import Task

from .api import TodoistClient
from .utils import format_label_with_color, extract_task_id_from_row_key, format_project_with_color
from .keybindings import get_keybindings
from rich.text import Text
from .screens import (
    DeleteConfirmScreen,
    ProjectSelectScreen,
    ChangeProjectScreen,
    AddTaskScreen,
    EditTaskScreen,
    LabelManagementScreen,
    FilterSelectScreen,
)

logger = logging.getLogger(__name__)


class TodoistTUI(App[None]):
    """A Textual TUI for Todoist tasks."""

    TITLE = "Tuidoist"
    CSS_PATH = "styles.tcss"
    BINDINGS = get_keybindings("main_app")  # type: ignore[assignment]

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.client = TodoistClient()
        self.active_project_id: Optional[str] = None  # None means show all projects
        self.active_filter: Optional[str] = None  # Current active filter (None = no filter)
        self.active_filter_name: str = "All Tasks"  # Display name for current filter
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
            
            # Fetch filters to get user-defined filters
            self.client.fetch_filters()
            
            # Fetch tasks
            tasks = self.client.fetch_tasks()
            self.call_from_thread(self.update_table, tasks)
        except Exception as e:
            logger.error(f"An error occurred during fetch: {e}", exc_info=True)
            self.call_from_thread(self.update_table_error, e)

    def update_table(self, tasks: List[Task]) -> None:
        """Update the DataTable with tasks."""
        logger.info(f"UPDATE_TABLE called with {len(tasks)} tasks")
        logger.info(f"Current active_filter: '{self.active_filter}', active_filter_name: '{self.active_filter_name}'")
        logger.info(f"Tasks cache before refresh: {len(self.client.tasks_cache)} tasks")
        logger.info(f"Tasks cache contents: {[t.content[:30] + '...' if len(t.content) > 30 else t.content for t in self.client.tasks_cache[:3]]}")
        self._refresh_table_display()

    def _refresh_table_display(self) -> None:
        """Refresh the table display with current filter settings."""
        logger.info(f"_REFRESH_TABLE_DISPLAY called")
        logger.info(f"Tasks cache has {len(self.client.tasks_cache)} tasks")
        logger.info(f"Active project ID: {self.active_project_id}")
        logger.info(f"Active filter: '{self.active_filter}', filter name: '{self.active_filter_name}'")
        
        table = self.query_one(DataTable)
        table.clear()
        
        # Filter tasks based on active project
        if self.active_project_id is None:
            tasks_to_show = self.client.tasks_cache
            logger.info(f"Showing all projects: {len(tasks_to_show)} tasks")
        else:
            tasks_to_show = [
                task for task in self.client.tasks_cache 
                if isinstance(task, Task) and task.project_id == self.active_project_id
            ]
            logger.info(f"Filtering by project {self.active_project_id}: {len(tasks_to_show)} tasks")
        
        if not tasks_to_show:
            if self.active_project_id is None:
                table.add_row("No tasks found.", "", "", "")
                logger.info("No tasks found (all projects)")
            else:
                project_name = self.get_active_project_name()
                table.add_row(f"No tasks found in {project_name}.", "", "", "")
                logger.info(f"No tasks found in project {project_name}")
        else:
            logger.info(f"Adding {len(tasks_to_show)} tasks to table")
            for task in tasks_to_show:
                if isinstance(task, Task):
                    due_date = getattr(task.due, 'date', 'N/A')
                    
                    # Format project name with color
                    project_display = format_project_with_color(
                        task.project_id,
                        self.client.project_name_map,
                        self.client.project_color_map
                    )
                    
                    # Format labels for display with colors
                    label_objects: List[Text] = []
                    if task.labels:  # Check if labels exist and are not None
                        for label_id in task.labels:
                            formatted_label = format_label_with_color(
                                label_id,
                                self.client.label_name_map,
                                self.client.label_color_map,
                                self.client.label_by_name
                            )
                            label_objects.append(formatted_label)
                    
                    # Combine Rich Text objects with commas
                    if label_objects:
                        labels_display = Text("")
                        for i, label_obj in enumerate(label_objects):
                            if i > 0:
                                labels_display.append(", ")
                            labels_display.append(label_obj)
                    else:
                        labels_display = Text("")
                    
                    # Use task.id as the row key (internal identifier)
                    table.add_row(task.content, due_date, project_display, labels_display, key=task.id)
                    logger.debug(f"Added task: {task.content[:50]}...")
                else:
                    logger.warning(f"Skipping non-task item: {task}")
        
        # Set cursor to first row if any
        if tasks_to_show:
            table.cursor_type = "row"
            table.cursor_coordinate = Coordinate(0, 0)
        
        # Update the title to show active project and filter
        project_name = self.get_active_project_name()
        if self.active_filter:
            self.title = f"Tuidoist - {project_name} - {self.active_filter_name}"
            logger.info(f"Updated title to: {self.title}")
        else:
            self.title = f"Tuidoist - {project_name}"
            logger.info(f"Updated title to: {self.title}")
        
        logger.info("_refresh_table_display completed")

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
        logger.info(f"ACTION_REFRESH called with active_filter: '{self.active_filter}'")
        
        # Fetch fresh data from the server
        self.client.fetch_projects() 
        self.client.fetch_labels()
        self.client.fetch_filters()
        
        # Re-apply the current filter if one is active
        if self.active_filter:
            logger.info(f"Re-applying active filter: '{self.active_filter}'")
            def fetch_with_filter():
                if self.active_filter is not None:  # Type guard
                    return self.fetch_filtered_tasks(self.active_filter)
            self.run_worker(fetch_with_filter, thread=True)
        else:
            logger.info("No active filter, fetching all tasks")
            # Fetch all tasks and refresh display
            self.client.fetch_tasks()
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
        # Ensure projects are fetched before showing the modal
        if not self.client.projects_cache:
            logger.info("Fetching projects before showing modal...")
            try:
                self.client.fetch_projects()
                logger.info(f"Successfully fetched {len(self.client.projects_cache)} projects for modal")
            except Exception as e:
                logger.error(f"Failed to fetch projects for modal: {e}")
                # Continue anyway - the modal will show the error
        
        if self.client.projects_cache:
            self.push_screen(ProjectSelectScreen(
                self.client.projects_cache, 
                self.active_project_id,
                self.client.project_color_map
            ))

    def set_active_project(self, project_id: Optional[str] = None) -> None:
        """Set the active project and refresh the display."""
        logger.info(f"SET_ACTIVE_PROJECT called with project_id: '{project_id}'")
        self.active_project_id = project_id
        
        # Log debug info about project mapping
        if project_id is not None:
            project_name = self.client.get_project_name(project_id)
            logger.info(f"Project ID '{project_id}' maps to name: '{project_name}'")
            logger.info(f"Available projects in map: {list(self.client.project_name_map.keys())}")
        
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
                    list(self.client.project_name_map.items()),
                    self.client.project_color_map
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

    def action_show_filter_modal(self) -> None:
        """Show the filter selection modal."""
        # Ensure filters are fetched before showing the modal
        if not self.client.filters_cache:
            logger.info("Fetching filters before showing modal...")
            try:
                self.client.fetch_filters()
                logger.info(f"Successfully fetched {len(self.client.filters_cache)} filters for modal")
            except Exception as e:
                logger.error(f"Failed to fetch filters for modal: {e}")
                # Continue anyway - the modal will show the error
        
        self.push_screen(FilterSelectScreen())

    def set_active_filter(self, filter_query: Optional[str], filter_name: str) -> None:
        """Set the active filter and refresh the display."""
        logger.info(f"SET_ACTIVE_FILTER called with query='{filter_query}', name='{filter_name}'")
        self.apply_filter(filter_query, filter_name)

    def fetch_filtered_tasks(self, filter_query: str) -> None:
        """Fetch tasks using a filter query."""
        try:
            logger.info(f"FETCH_FILTERED_TASKS called with filter_query: '{filter_query}'")
            
            # Fetch projects, labels, and filters first
            logger.info("Fetching projects, labels, and filters...")
            self.client.fetch_projects()
            self.client.fetch_labels()
            self.client.fetch_filters()
            
            # Fetch tasks with filter
            logger.info(f"About to call client.fetch_tasks_with_filter with query: '{filter_query}'")
            tasks = self.client.fetch_tasks_with_filter(filter_query)
            logger.info(f"Got {len(tasks)} tasks from fetch_tasks_with_filter")
            self.call_from_thread(self.update_table, tasks)
        except Exception as e:
            logger.error(f"An error occurred during filtered fetch: {e}", exc_info=True)
            self.call_from_thread(self.update_table_error, e)

    def apply_filter(self, filter_query: Optional[str], filter_name: str) -> None:
        """Apply a filter and refresh tasks."""
        logger.info(f"APPLY_FILTER called with query='{filter_query}', name='{filter_name}'")
        self.active_filter = filter_query
        self.active_filter_name = filter_name
        logger.info(f"Set active_filter='{self.active_filter}', active_filter_name='{self.active_filter_name}'")
        
        if filter_query:
            logger.info(f"Starting filtered fetch with query: '{filter_query}'")
            # Create a lambda wrapper for the run_worker call
            def fetch_with_filter():
                return self.fetch_filtered_tasks(filter_query)
            self.run_worker(fetch_with_filter, thread=True)
        else:
            logger.info("Starting fetch of all tasks (no filter)")
            # Fetch all tasks (no filter)
            self.run_worker(self.fetch_tasks, thread=True)


def setup_config():
    """Interactive setup to configure API token."""
    from .config import get_config_directory
    
    print("🔧 Tuidoist Configuration Setup")
    print("=" * 35)
    print()
    
    # Check if token already exists
    from .config import TODOIST_API_TOKEN
    if TODOIST_API_TOKEN:
        print("✅ API token is already configured!")
        print("Current token status: Found and loaded")
        print()
        print("If you want to change your token, continue with this setup.")
        print()
    
    print("Choose how to configure your Todoist API token:")
    print()
    print("1. Save to config file (recommended for production)")
    print("2. Environment variable instructions")
    print("3. Exit without changes")
    print()
    
    choice = input("Enter your choice (1-3): ").strip()
    
    if choice == "1":
        # Get API token from user
        print()
        print("📋 Get your API token from: https://todoist.com/prefs/integrations")
        print()
        token = input("Enter your Todoist API token: ").strip()
        
        if not token:
            print("❌ No token provided. Setup cancelled.")
            return
        
        # Create config directory using XDG specification
        config_dir = get_config_directory()
        config_file = config_dir / "config.toml"
        
        # Write config file
        try:
            with open(config_file, 'w') as f:
                f.write(f'api_token = "{token}"\n')
            
            print(f"✅ API token saved to: {config_file}")
            print()
            print("You can now run 'tuidoist' to start the application!")
            
        except Exception as e:
            print(f"❌ Failed to save config file: {e}")
    
    elif choice == "2":
        print()
        print("📋 Environment Variable Setup:")
        print()
        print("For development, you can use an environment variable:")
        print("  export TODOIST_API_TOKEN='your_token_here'")
        print()
        print("Or create a .env file in your project directory:")
        print("  echo 'TODOIST_API_TOKEN=your_token_here' > .env")
        print()
        print("Get your API token from: https://todoist.com/prefs/integrations")
    
    elif choice == "3":
        print("Setup cancelled.")
    
    else:
        print("❌ Invalid choice. Setup cancelled.")

def main():
    """Entry point for the application."""
    import sys
    
    # Check for setup command
    if len(sys.argv) > 1 and sys.argv[1] == "--setup-config":
        setup_config()
        return
    
    app = TodoistTUI()
    app.run()


if __name__ == "__main__":
    main()
