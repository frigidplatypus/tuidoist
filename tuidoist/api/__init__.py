"""Todoist API client wrapper.

This module integrates with the Todoist REST API v1.
Canonical API documentation: https://developer.todoist.com/api/v1/

Always refer to the official documentation for the latest endpoint specifications,
request/response formats, authentication methods, and rate limits.
"""

import logging
from typing import List, Dict, Optional, Any, cast
from todoist_api_python.api import TodoistAPI
from todoist_api_python.models import Task, Project
from todoist_api_python.models import Label as TodoistLabel

from ..config import TODOIST_API_TOKEN

logger = logging.getLogger(__name__)


class TodoistClient:
    """Wrapper around the Todoist API client with caching and convenience methods."""
    
    def __init__(self):
        """Initialize the Todoist API client."""
        self.api = TodoistAPI(TODOIST_API_TOKEN) if TODOIST_API_TOKEN and isinstance(TODOIST_API_TOKEN, str) else None
        self.project_name_map: Dict[str, str] = {}  # Maps project ID to project name
        self.project_color_map: Dict[str, str] = {}  # Maps project ID to project color
        self.label_name_map: Dict[str, str] = {}  # Maps label ID to label name
        self.label_color_map: Dict[str, str] = {}  # Maps label ID to label color
        self.label_by_name: Dict[str, str] = {}  # Maps label name to label name (for reverse lookup)
        self.filter_name_map: Dict[str, str] = {}  # Maps filter ID to filter name
        self.filter_color_map: Dict[str, str] = {}  # Maps filter ID to filter color
        self.projects_cache: List[Any] = []  # Store the latest fetched projects
        self.labels_cache: List[Any] = []  # Store the latest fetched labels
        self.tasks_cache: List[Any] = []  # Store the latest fetched tasks
        self.filters_cache: List[Any] = []  # Store the latest fetched filters
    
    @property
    def is_initialized(self) -> bool:
        """Check if the API client is properly initialized."""
        return self.api is not None
    
    def fetch_projects(self) -> List[Project]:
        """Fetch projects from the Todoist API and update cache."""
        if not self.api:
            return []
        
        try:
            logger.info("Fetching projects...")
            projects = list(self.api.get_projects())
            
            # Handle potentially nested list from the API response
            if projects and isinstance(projects[0], list):
                projects_to_process = cast(List[Project], projects[0])
            else:
                projects_to_process = cast(List[Project], projects)
            
            self.project_name_map = {}
            self.project_color_map = {}
            for project in projects_to_process:
                if isinstance(project, Project):
                    self.project_name_map[project.id] = project.name
                    self.project_color_map[project.id] = project.color
                    logger.debug(f"Loaded project: {project.name} (ID: {project.id}) -> color: {project.color}")
            
            self.projects_cache = projects_to_process
            logger.info(f"Fetched {len(projects_to_process)} projects")
            return projects_to_process
        except Exception as e:
            logger.error(f"Failed to fetch projects: {e}", exc_info=True)
            return []
    
    def fetch_labels(self) -> List[TodoistLabel]:
        """Fetch labels from the Todoist API and update cache."""
        if not self.api:
            return []
        
        try:
            logger.info("Fetching labels...")
            labels = list(self.api.get_labels())
            
            # Handle potentially nested list from the API response
            if labels and isinstance(labels[0], list):
                labels_to_process = cast(List[TodoistLabel], labels[0])
            else:
                labels_to_process = cast(List[TodoistLabel], labels)
            
            self.label_name_map = {}
            self.label_color_map = {}
            self.label_by_name = {}
            
            for label in labels_to_process:
                if isinstance(label, TodoistLabel):
                    self.label_name_map[label.id] = label.name
                    self.label_color_map[label.id] = label.color
                    self.label_by_name[label.name] = label.name  # Name to name mapping
                    logger.info(f"Loaded label: {label.name} (ID: {label.id}) -> color: {label.color}")
            
            self.labels_cache = labels_to_process
            logger.info(f"Fetched {len(labels_to_process)} labels")
            return labels_to_process
        except Exception as e:
            logger.error(f"Failed to fetch labels: {e}", exc_info=True)
            return []
    
    def fetch_filters(self) -> List[Dict[str, Any]]:
        """Fetch filters from the Todoist API using the sync endpoint.
        
        Note: The Python SDK doesn't have direct filter support, so we use
        requests to call the sync API directly to get user-defined filters.
        """
        if not self.api:
            return []
        
        try:
            import requests
            logger.info("Fetching filters from sync API...")
            
            # Use the sync endpoint to get filters
            url = "https://api.todoist.com/sync/v9/sync"
            headers = {
                "Authorization": f"Bearer {TODOIST_API_TOKEN}",
                "Content-Type": "application/x-www-form-urlencoded"
            }
            data = {
                "sync_token": "*",
                "resource_types": '["filters"]'
            }
            
            response = requests.post(url, headers=headers, data=data)
            response.raise_for_status()
            
            sync_data = response.json()
            filters = sync_data.get("filters", [])
            
            # Clear and update filter maps
            self.filter_name_map = {}
            self.filter_color_map = {}
            
            self.filters_cache = filters
            logger.info(f"Fetched {len(filters)} filters")
            
            for filter_item in filters:
                if isinstance(filter_item, dict) and "id" in filter_item:
                    filter_id = str(filter_item["id"])
                    filter_name = filter_item.get("name", f"Filter {filter_id}")
                    filter_color = filter_item.get("color", "charcoal")
                    
                    self.filter_name_map[filter_id] = filter_name
                    self.filter_color_map[filter_id] = filter_color
                    
                    logger.info(f"Filter: {filter_name} (ID: {filter_id}) - Color: {filter_color} - Query: {filter_item.get('query')}")
            
            return filters
        except Exception as e:
            logger.error(f"Failed to fetch filters: {e}", exc_info=True)
            return []
    
    def fetch_tasks(self) -> List[Task]:
        """Fetch tasks from the Todoist API and update cache."""
        if not self.api:
            return []
        
        try:
            logger.info("Fetching tasks...")
            tasks = list(self.api.get_tasks())
            logger.info(f"API returned: {tasks}")  # Log the raw API response
            
            # Handle potentially nested list from the API response
            if tasks and isinstance(tasks[0], list):
                tasks_to_process = cast(List[Task], tasks[0])
            else:
                tasks_to_process = cast(List[Task], tasks)
            
            self.tasks_cache = tasks_to_process
            logger.info(f"Fetched {len(tasks_to_process)} tasks")
            return tasks_to_process
        except Exception as e:
            logger.error(f"Failed to fetch tasks: {e}", exc_info=True)
            return []
    
    def fetch_tasks_with_filter(self, filter_query: str) -> List[Task]:
        """Fetch tasks from the Todoist API using a filter query.
        
        Uses the SDK's filter_tasks method to apply Todoist's server-side filtering.
        """
        if not self.api:
            logger.error("API client not initialized")
            return []
        
        try:
            logger.info(f"CLIENT: fetch_tasks_with_filter called with query: '{filter_query}'")
            
            # Use the SDK's filter_tasks method for server-side filtering
            logger.info("CLIENT: About to call api.filter_tasks")
            filtered_tasks_iter = self.api.filter_tasks(query=filter_query)
            logger.info(f"CLIENT: Got iterator from filter_tasks: {filtered_tasks_iter}")
            
            # Convert the iterator to a list
            filtered_tasks = []
            logger.info("CLIENT: Converting iterator to list...")
            for i, task_batch in enumerate(filtered_tasks_iter):
                logger.info(f"CLIENT: Processing batch {i} with {len(task_batch)} tasks")
                filtered_tasks.extend(task_batch)
                # Limit to prevent infinite loops in case of API issues
                if i > 10:
                    logger.warning("CLIENT: Breaking after 10 batches to prevent infinite loop")
                    break
            
            logger.info(f"CLIENT: Total filtered tasks collected: {len(filtered_tasks)}")
            self.tasks_cache = filtered_tasks
            logger.info(f"CLIENT: Updated tasks_cache with {len(filtered_tasks)} tasks")
            return filtered_tasks
                
        except Exception as e:
            logger.error(f"CLIENT: Failed to fetch filtered tasks: {e}", exc_info=True)
            return []

    def complete_task(self, task_id: str) -> bool:
        """Complete a task."""
        if not self.api:
            return False
        
        try:
            self.api.complete_task(task_id)
            logger.info(f"Completed task: {task_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to complete task {task_id}: {e}")
            return False
    
    def delete_task(self, task_id: str) -> bool:
        """Delete a task."""
        if not self.api:
            return False
        
        try:
            self.api.delete_task(task_id)
            logger.info(f"Deleted task: {task_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete task {task_id}: {e}")
            return False
    
    def add_task_quick(self, text: str) -> Optional[Task]:
        """Add a task using natural language processing."""
        if not self.api:
            return None
        
        try:
            new_task = self.api.add_task_quick(text=text)
            logger.info(f"Added task: {new_task.content} (ID: {new_task.id})")
            return new_task
        except Exception as e:
            logger.error(f"Failed to add task: {e}")
            return None
    
    def update_task(self, task_id: str, content: str, due_string: Optional[str] = None) -> Optional[Task]:
        """Update a task."""
        if not self.api:
            return None
        
        try:
            updated_task = self.api.update_task(
                task_id=task_id,
                content=content,
                due_string=due_string if due_string else None
            )
            logger.info(f"Updated task: {updated_task.content} (ID: {updated_task.id})")
            return updated_task
        except Exception as e:
            logger.error(f"Failed to update task {task_id}: {e}")
            return None
    
    def update_task_priority(self, task_id: str, priority: int) -> Optional[Task]:
        """Update task priority.
        
        Args:
            task_id: The ID of the task to update
            priority: Priority level (1=normal, 2=high, 3=very high, 4=urgent)
        
        Returns:
            The updated task or None if the update failed
        """
        if not self.api:
            return None
        
        try:
            updated_task = self.api.update_task(
                task_id=task_id,
                priority=priority
            )
            logger.info(f"Updated task priority: {updated_task.content} (ID: {updated_task.id}) to priority {priority}")
            return updated_task
        except Exception as e:
            logger.error(f"Failed to update task priority {task_id}: {e}")
            return None
    
    def update_task_with_natural_language(self, task_id: str, content_with_nl: str) -> Optional[Task]:
        """Update a task by parsing natural language elements like #project and @labels."""
        if not self.api:
            return None
        
        try:
            # Parse the content for natural language elements
            parsed = self._parse_natural_language_elements(content_with_nl)
            
            # Update the task with parsed elements (excluding project_id which needs separate handling)
            updated_task = self.api.update_task(
                task_id=task_id,
                content=parsed['content'],
                due_string=parsed['due_string'],
                labels=parsed['labels'] if parsed['labels'] else None
            )
            
            # Handle project change separately if needed
            if parsed['project_id']:
                self.move_task(task_id, parsed['project_id'])
            
            logger.info(f"Updated task with natural language: {updated_task.content} (ID: {updated_task.id})")
            return updated_task
        except Exception as e:
            logger.error(f"Failed to update task {task_id} with natural language: {e}")
            return None
    
    def _parse_natural_language_elements(self, content: str) -> Dict[str, Any]:
        """Parse natural language elements from task content."""
        import re
        
        result = {
            'content': content,
            'due_string': None,
            'project_id': None,
            'labels': []
        }
        
        # Parse project (#ProjectName)
        project_match = re.search(r'#(\w+)', content)
        if project_match:
            project_name = project_match.group(1)
            # Find project ID by name (case-insensitive)
            for pid, pname in self.project_name_map.items():
                if pname.lower() == project_name.lower():
                    result['project_id'] = pid
                    break
            # Remove project from content
            result['content'] = re.sub(r'\s*#\w+', '', result['content']).strip()
        
        # Parse labels (@LabelName)
        label_matches = re.findall(r'@(\w+)', content)
        if label_matches:
            for label_name in label_matches:
                # Find label name (case-insensitive) - API expects names, not IDs
                for lid, lname in self.label_name_map.items():
                    if lname.lower() == label_name.lower():
                        result['labels'].append(lname)  # Use label name, not ID
                        break
                else:
                    # If label doesn't exist, try to use the typed name directly
                    result['labels'].append(label_name)
            # Remove labels from content
            result['content'] = re.sub(r'\s*@\w+', '', result['content']).strip()
        
        # Parse due dates (basic patterns)
        due_patterns = [
            r'\b(today|tomorrow|yesterday)\b',
            r'\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b',
            r'\b\d{1,2}[/-]\d{1,2}([/-]\d{2,4})?\b',
            r'\bat \d{1,2}:\d{2}( ?[ap]m)?\b',
            r'\b(next|this) (week|month|year)\b',
            r'\bin \d+ (day|week|month|year)s?\b'
        ]
        
        for pattern in due_patterns:
            match = re.search(pattern, result['content'], re.IGNORECASE)
            if match:
                result['due_string'] = match.group(0)
                # Remove due date from content
                result['content'] = re.sub(pattern, '', result['content'], flags=re.IGNORECASE).strip()
                break
        
        return result
    
    def move_task(self, task_id: str, project_id: str) -> bool:
        """Move a task to a different project."""
        if not self.api:
            return False
        
        try:
            self.api.move_task(task_id=task_id, project_id=project_id)
            logger.info(f"Moved task {task_id} to project {project_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to move task {task_id} to project {project_id}: {e}")
            return False
    
    def get_project_name(self, project_id: str) -> str:
        """Get project name by ID."""
        project_name = self.project_name_map.get(project_id, 'Unknown Project')
        if project_name == 'Unknown Project':
            logger.warning(f"Project ID '{project_id}' not found in project_name_map. Available keys: {list(self.project_name_map.keys())}")
        return project_name
    
    def get_project_color(self, project_id: str) -> Optional[str]:
        """Get project color by ID."""
        return self.project_color_map.get(project_id)
    
    def get_label_name(self, label_id: str) -> str:
        """Get label name by ID."""
        return self.label_name_map.get(label_id, label_id)
    
    def get_label_color(self, label_id: str) -> Optional[str]:
        """Get label color by ID."""
        return self.label_color_map.get(label_id)

    def get_filter_name(self, filter_id: str) -> str:
        """Get filter name by ID."""
        return self.filter_name_map.get(filter_id, filter_id)
    
    def get_filter_color(self, filter_id: str) -> Optional[str]:
        """Get filter color by ID."""
        return self.filter_color_map.get(filter_id)

    def update_task_labels(self, task_id: str, label_names: List[str]) -> bool:
        """Update a task's labels."""
        if not self.api:
            return False
        
        try:
            self.api.update_task(task_id=task_id, labels=label_names)
            logger.info(f"Updated task {task_id} labels to: {label_names}")
            
            # Refresh the tasks cache to reflect the updated labels
            self.fetch_tasks()
            
            return True
        except Exception as e:
            logger.error(f"Failed to update task {task_id} labels: {e}")
            return False

    def create_label(self, name: str, color: str = "charcoal") -> bool:
        """Create a new label."""
        if not self.api:
            return False
        
        try:
            new_label = self.api.add_label(name=name, color=color)
            logger.info(f"Created new label: {new_label.name} (ID: {new_label.id})")
            # Update caches
            self.label_name_map[new_label.id] = new_label.name
            self.label_color_map[new_label.id] = new_label.color
            self.label_by_name[new_label.name] = new_label.name
            return True
        except Exception as e:
            logger.error(f"Failed to create label '{name}': {e}")
            return False
    
    def get_filter_by_id(self, filter_id: str) -> Optional[Dict[str, Any]]:
        """Get a filter by its ID from the cache."""
        for filter_obj in self.filters_cache:
            if isinstance(filter_obj, dict) and str(filter_obj.get("id")) == str(filter_id):
                return filter_obj
        return None
