#!/usr/bin/env python3
"""Test script to verify the filter selection screen functionality."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from tuidoist.api import TodoistClient
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_filter_display():
    """Test how filters would be displayed in the FilterSelectScreen."""
    print("Testing filter display logic...")
    
    # Initialize client
    client = TodoistClient()
    
    if not client.is_initialized:
        print("ERROR: Todoist client not initialized - check API token")
        return False
    
    print("Todoist client initialized successfully")
    
    # Fetch filters
    filters = client.fetch_filters()
    print(f"Fetched {len(filters)} filters from API")
    
    # Simulate the FilterSelectScreen logic
    print("\nSimulating FilterSelectScreen display:")
    
    # Built-in filters
    builtin_filters = [
        ("all", "All Tasks", "Show all tasks"),
        ("today", "Today", "Tasks due today"),
        ("this_week", "This Week", "Tasks due this week"),
        ("overdue", "Overdue", "Tasks that are overdue"),
    ]
    
    print("\nBuilt-in filters:")
    for filter_key, filter_name, description in builtin_filters:
        print(f"  - {filter_name}: {description}")
    
    # User-defined filters
    if hasattr(client, 'filters_cache') and client.filters_cache:
        print(f"\nUser-defined filters ({len(client.filters_cache)} found):")
        
        for filter_obj in client.filters_cache:
            if isinstance(filter_obj, dict) and "id" in filter_obj and "name" in filter_obj:
                filter_id = str(filter_obj["id"])
                filter_name = filter_obj["name"]
                filter_query = filter_obj.get("query", "")
                description = f"Query: {filter_query}" if filter_query else "User-defined filter"
                
                print(f"  - {filter_name} (ID: {filter_id}): {description}")
    else:
        print("\nNo user-defined filters found")
    
    print(f"\nTotal filters that would be displayed: {len(builtin_filters) + len(client.filters_cache)}")
    
    return True

if __name__ == "__main__":
    success = test_filter_display()
    if success:
        print("\n✓ Filter display test completed successfully")
    else:
        print("\n✗ Filter display test failed")
    sys.exit(0 if success else 1)
