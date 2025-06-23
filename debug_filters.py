#!/usr/bin/env python3
"""Debug script to check filter fetching."""

import os
from tuidoist.api import TodoistClient

def debug_filters():
    print("🔍 Debugging filter fetching...")
    
    # Check API token
    token = os.environ.get("TODOIST_API_TOKEN")
    if not token:
        print("❌ No TODOIST_API_TOKEN found in environment")
        return
    
    print(f"✅ API token found: {token[:10]}...")
    
    # Initialize client
    client = TodoistClient()
    if not client.is_initialized:
        print("❌ Client not initialized")
        return
    
    print("✅ Client initialized")
    
    # Fetch filters
    print("\n📥 Fetching filters...")
    filters = client.fetch_filters()
    
    print(f"📊 Raw filter response: {len(filters)} filters")
    print(f"📊 Filters cache: {len(client.filters_cache)} filters")
    print(f"📊 Filter name map: {len(client.filter_name_map)} entries")
    
    print("\n🔍 Filter details:")
    for i, filter_obj in enumerate(filters):
        print(f"  {i+1}. {filter_obj}")
    
    print("\n🗂️ Filter name map:")
    for filter_id, name in client.filter_name_map.items():
        print(f"  {filter_id}: {name}")

if __name__ == "__main__":
    debug_filters()
