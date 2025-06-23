#!/usr/bin/env python3
"""Test script to verify filter fetching functionality."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from tuidoist.api import TodoistClient
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_filter_fetching():
    """Test the filter fetching functionality."""
    print("Testing filter fetching...")
    
    # Initialize client
    client = TodoistClient()
    
    if not client.is_initialized:
        print("ERROR: Todoist client not initialized - check API token")
        return False
    
    print("Todoist client initialized successfully")
    
    # Fetch filters
    filters = client.fetch_filters()
    
    print(f"\nFetched {len(filters)} filters:")
    for i, filter_obj in enumerate(filters, 1):
        if isinstance(filter_obj, dict):
            name = filter_obj.get('name', 'N/A')
            query = filter_obj.get('query', 'N/A')
            filter_id = filter_obj.get('id', 'N/A')
            print(f"  {i}. {name} (ID: {filter_id})")
            print(f"     Query: {query}")
        else:
            print(f"  {i}. Invalid filter object: {filter_obj}")
    
    # Check cache
    print(f"\nCache status:")
    print(f"  filters_cache: {len(client.filters_cache)} items")
    print(f"  filter_name_map: {len(client.filter_name_map)} items")
    
    if client.filters_cache:
        print("\nCache contents:")
        for filter_obj in client.filters_cache:
            if isinstance(filter_obj, dict):
                print(f"  - {filter_obj.get('name', 'N/A')} -> {filter_obj.get('query', 'N/A')}")
    
    return len(filters) > 0

if __name__ == "__main__":
    success = test_filter_fetching()
    if success:
        print("\n✓ Filter fetching test completed successfully")
    else:
        print("\n✗ Filter fetching test failed")
    sys.exit(0 if success else 1)
