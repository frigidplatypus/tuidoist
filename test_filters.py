#!/usr/bin/env python3
"""Test script to verify the filter functionality works."""

import sys
import os
import logging

# Add the tuidoist package to the path
sys.path.insert(0, '/home/justin/development/python/tuidoist')

from tuidoist.api import TodoistClient
from tuidoist.config import TODOIST_API_TOKEN

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_filter_functionality():
    """Test the filter functionality."""
    print("Testing Todoist filter functionality...")
    
    # Check if API token is available
    if not TODOIST_API_TOKEN:
        print("❌ No TODOIST_API_TOKEN environment variable found")
        print("   Please set your Todoist API token:")
        print("   export TODOIST_API_TOKEN='your_token_here'")
        return False
    
    print(f"✅ API token found: {TODOIST_API_TOKEN[:10]}...")
    
    # Initialize client
    client = TodoistClient()
    
    if not client.is_initialized:
        print("❌ Failed to initialize Todoist client")
        return False
    
    print("✅ Todoist client initialized")
    
    # Test fetching filters
    print("\nTesting filter fetching...")
    try:
        filters = client.fetch_filters()
        print(f"✅ Fetched {len(filters)} user-defined filters")
        
        if filters:
            print("\nUser filters found:")
            for filter_obj in filters:
                if isinstance(filter_obj, dict):
                    name = filter_obj.get("name", "Unnamed")
                    query = filter_obj.get("query", "No query")
                    print(f"  - {name}: {query}")
        else:
            print("  No user-defined filters found")
    
    except Exception as e:
        print(f"❌ Error fetching filters: {e}")
        return False
    
    # Test fetching tasks with built-in filter
    print("\nTesting built-in filter (today)...")
    try:
        today_tasks = client.fetch_tasks_with_filter("today")
        print(f"✅ Fetched {len(today_tasks)} tasks due today")
    except Exception as e:
        print(f"❌ Error fetching tasks with 'today' filter: {e}")
        return False
    
    # Test fetching all tasks
    print("\nTesting regular task fetching...")
    try:
        all_tasks = client.fetch_tasks()
        print(f"✅ Fetched {len(all_tasks)} total tasks")
    except Exception as e:
        print(f"❌ Error fetching all tasks: {e}")
        return False
    
    print("\n🎉 All tests passed! Filter functionality appears to be working.")
    return True

if __name__ == "__main__":
    success = test_filter_functionality()
    sys.exit(0 if success else 1)
