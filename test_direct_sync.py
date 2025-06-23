#!/usr/bin/env python3
"""Simple test to verify filter fetching works."""

import os
import sys
import requests

# Get API token
token = os.environ.get("TODOIST_API_TOKEN")
if not token:
    print("❌ No TODOIST_API_TOKEN found")
    sys.exit(1)

print(f"✅ Using API token: {token[:10]}...")

# Test the sync endpoint directly
sync_url = "https://api.todoist.com/sync/v1/sync"
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/x-www-form-urlencoded"
}
data = {
    "sync_token": "*",
    "resource_types": '["filters"]'
}

print("🔄 Making request to sync endpoint...")

try:
    response = requests.post(sync_url, headers=headers, data=data)
    response.raise_for_status()
    
    sync_data = response.json()
    filters = sync_data.get("filters", [])
    
    print(f"✅ Response received: {response.status_code}")
    print(f"📊 Found {len(filters)} filters")
    
    for i, filter_obj in enumerate(filters, 1):
        print(f"  {i}. Name: {filter_obj.get('name', 'N/A')}")
        print(f"     ID: {filter_obj.get('id', 'N/A')}")
        print(f"     Query: {filter_obj.get('query', 'N/A')}")
        print()
        
except Exception as e:
    print(f"❌ Error: {e}")
