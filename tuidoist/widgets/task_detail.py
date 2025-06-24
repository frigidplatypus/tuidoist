"""Task detail widget for displaying comprehensive task information."""

from typing import Optional
from textual.widgets import Static
from textual.reactive import reactive
from todoist_api_python.models import Task
from datetime import datetime, timezone


class TaskDetailWidget(Static):
    """Widget to display detailed task information in a simple format."""
    
    current_task: reactive[Optional[Task]] = reactive(None, layout=True)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.client = None  # Will be set by parent app
    
    def watch_current_task(self, task: Optional[Task]) -> None:
        """Update the display when the current task changes."""
        self.update_display(task)
    
    def update_task(self, task: Optional[Task]) -> None:
        """Update the displayed task details."""
        self.current_task = task
    
    def update_display(self, task: Optional[Task]) -> None:
        """Update the widget content with task details."""
        if task is None:
            self.update("Select a task to view additional details")
            return
        
        content = self._render_task_details(task)
        self.update(content)
    
    def _render_task_details(self, task: Task) -> str:
        """Render the specific task details requested."""
        details = []
        
        # Description
        if task.description and task.description.strip():
            details.append("📄 Description:")
            desc = task.description[:200] + "..." if len(task.description) > 200 else task.description
            details.append(f"  {desc}")
            details.append("")
        
        # Due date and time
        if task.due:
            due_text = f"⏰ Due: {task.due.date}"
            if hasattr(task.due, 'datetime') and task.due.datetime:
                due_text += f" at {task.due.datetime.strftime('%H:%M')}"
            if hasattr(task.due, 'timezone') and task.due.timezone:
                due_text += f" ({task.due.timezone})"
            details.append(due_text)
        
        # Deadline (if different from due)
        if task.deadline:
            deadline_text = "⚠️ Deadline: "
            # Handle different deadline formats
            if hasattr(task.deadline, 'date') and task.deadline.date:
                deadline_text += task.deadline.date.strftime('%Y-%m-%d')
                if hasattr(task.deadline, 'datetime') and task.deadline.datetime:
                    deadline_text += f" at {task.deadline.datetime.strftime('%H:%M')}"
                if hasattr(task.deadline, 'timezone') and task.deadline.timezone:
                    deadline_text += f" ({task.deadline.timezone})"
            else:
                # If deadline is just a string or other format
                deadline_text += str(task.deadline)
            details.append(deadline_text)
        
        # Duration
        if task.duration:
            duration_text = str(task.duration)
            if hasattr(task.duration, 'amount') and hasattr(task.duration, 'unit'):
                duration_text = f"{task.duration.amount} {task.duration.unit}"
                if task.duration.amount != 1:
                    duration_text += "s"
            details.append(f"⏱️ Duration: {duration_text}")
        
        # Created date
        if task.created_at:
            details.append(f"🕐 Created: {task.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Updated date
        if task.updated_at:
            details.append(f"🕑 Updated: {task.updated_at.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # If no details to show
        if not details:
            return "No additional details available"
        
        return "\n".join(details)
