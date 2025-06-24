"""Main application module for the Todoist TUI.

This application integrates with the Todoist REST API v1.
Canonical API documentation: https://developer.todoist.com/api/v1/
"""

import logging
from typing import Optional, List, Any
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, DataTable
from textual.containers import Vertical, Container
from textual.coordinate import Coordinate
from todoist_api_python.models import Task

from .api import TodoistClient
from .utils import format_label_with_color, extract_task_id_from_row_key, format_project_with_color, format_priority_indicator
from .keybindings import get_keybindings
from .widgets import TaskDetailWidget, HorizontalSplitContainer
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
        self.show_details: bool = True  # Toggle for showing/hiding details panel

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        
        # Always create split layout, but adjust visibility via CSS in toggle
        self.tasks_table = DataTable(id="tasks_table")
        self.task_detail_widget = TaskDetailWidget(id="task_detail_widget")
        
        yield HorizontalSplitContainer(
            top_widget=self.tasks_table,
            bottom_widget=self.task_detail_widget,
            id="split_container"
        )
        
        yield Footer()

    def on_mount(self) -> None:
        """Called when app starts."""
        table = self.query_one(DataTable)
        table.add_columns("Task", "Due Date", "Project", "Labels")
        
        if not self.client.is_initialized:
            table.add_row("[bold red]Error: TODOIST_API_TOKEN not set.[/bold red]", "", "", "")
            return
        
        self.run_worker(self.fetch_tasks, thread=True)

    def on_ready(self) -> None:
        """Called when the app is ready."""
        # Set up the task detail widget with client reference
        detail_widget = self.query_one("#task_detail_widget", TaskDetailWidget)
        detail_widget.client = self.client

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle task selection to update the details panel."""
        # Get the task ID from the selected row
        task_id = self.get_selected_row_key()
        if task_id is None:
            return
        
        actual_task_id = extract_task_id_from_row_key(task_id)
        if not actual_task_id:
            return
        
        # Find the corresponding Task object from our cache
        selected_task = None
        for task in self.client.tasks_cache:
            if isinstance(task, Task) and task.id == actual_task_id:
                selected_task = task
                break
        
        # Update the details panel (only if visible)
        if self.show_details:
            detail_widget = self.query_one("#task_detail_widget", TaskDetailWidget)
            detail_widget.update_task(selected_task)

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        """Handle task highlighting to update the details panel automatically."""
        if not self.show_details:
            return
            
        # Get the task ID from the highlighted row
        if event.row_key is None:
            return
            
        actual_task_id = extract_task_id_from_row_key(event.row_key.value)
        if not actual_task_id:
            return
        
        # Find the corresponding Task object from our cache
        selected_task = None
        for task in self.client.tasks_cache:
            if isinstance(task, Task) and task.id == actual_task_id:
                selected_task = task
                break
        
        # Update the details panel
        detail_widget = self.query_one("#task_detail_widget", TaskDetailWidget)
        detail_widget.update_task(selected_task)

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
                    
                    # Debug logging for task priority
                    logger.debug(f"Task '{task.content}' has priority: {task.priority} (type: {type(task.priority)})")
                    
                    # Format priority indicator and task content
                    priority_indicator = format_priority_indicator(task.priority)
                    task_content = Text("")
                    task_content.append(priority_indicator)
                    task_content.append(" ")  # Space between indicator and content
                    task_content.append(task.content)
                    
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
                    table.add_row(task_content, due_date, project_display, labels_display, key=task.id)
                    logger.debug(f"Added task: {task.content[:50]}...")
                else:
                    logger.warning(f"Skipping non-task item: {task}")
        
        # Set cursor to first row if any
        if tasks_to_show:
            table.cursor_type = "row"
            table.cursor_coordinate = Coordinate(0, 0)
            
            # Auto-update details panel with first task (if details are visible)
            if self.show_details:
                first_task = tasks_to_show[0] if isinstance(tasks_to_show[0], Task) else None
                if first_task:
                    detail_widget = self.query_one("#task_detail_widget", TaskDetailWidget)
                    detail_widget.update_task(first_task)
        
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

    def action_set_priority_1(self) -> None:
        """Set the selected task priority to 1 (highest - urgent/red)."""
        self._set_task_priority(4)  # API priority 4 = urgent
    
    def action_set_priority_2(self) -> None:
        """Set the selected task priority to 2 (high - very high/blue)."""
        self._set_task_priority(3)  # API priority 3 = very high
    
    def action_set_priority_3(self) -> None:
        """Set the selected task priority to 3 (medium - high/yellow)."""
        self._set_task_priority(2)  # API priority 2 = high
    
    def action_set_priority_4(self) -> None:
        """Set the selected task priority to 4 (lowest - normal/white)."""
        self._set_task_priority(1)  # API priority 1 = normal
    
    def action_clear_priority(self) -> None:
        """Clear the selected task priority (set to normal)."""
        self._set_task_priority(1)  # API priority 1 = normal
    
    def _set_task_priority(self, priority: int) -> None:
        """Helper method to set task priority."""
        task_id = self.get_selected_row_key()
        if task_id is not None:
            actual_task_id = extract_task_id_from_row_key(task_id)
            if actual_task_id:
                updated_task = self.client.update_task_priority(actual_task_id, priority)
                if updated_task:
                    # Refresh the task display to show the new priority indicator
                    self.action_refresh()
                else:
                    self.bell()
            else:
                self.bell()
        else:
            self.bell()

    def action_toggle_details(self) -> None:
        """Toggle the details panel visibility."""
        self.show_details = not self.show_details
        
        # Get the widgets directly
        tasks_table = self.query_one("#tasks_table", DataTable)
        detail_widget = self.query_one("#task_detail_widget", TaskDetailWidget)
        
        if self.show_details:
            # Show the details panel
            detail_widget.display = True
            tasks_table.styles.height = "60%"
            detail_widget.styles.height = "40%"
            
            # Set up the task detail widget with client reference if not already done
            if not detail_widget.client:
                detail_widget.client = self.client
            
            # Update with current task if any is selected
            current_row_key = self.get_selected_row_key()
            if current_row_key:
                actual_task_id = extract_task_id_from_row_key(current_row_key)
                if actual_task_id:
                    selected_task = None
                    for task in self.client.tasks_cache:
                        if isinstance(task, Task) and task.id == actual_task_id:
                            selected_task = task
                            break
                    if selected_task:
                        detail_widget.update_task(selected_task)
        else:
            # Hide the details panel and expand task list to full height
            detail_widget.display = False
            tasks_table.styles.height = "100%"
        
        # Force a refresh of the layout
        self.refresh(layout=True)

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
