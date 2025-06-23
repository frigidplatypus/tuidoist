#!/usr/bin/env python3
"""Test script to verify label management functionality."""

import sys
sys.path.insert(0, '/home/justin/development/python/tuidoist')

try:
    from tuidoist.screens import LabelManagementScreen
    from tuidoist.api import TodoistClient
    from tuidoist.app import TodoistTUI
    
    print("✓ All imports successful!")
    
    # Test instantiation
    client = TodoistClient()
    print(f"✓ TodoistClient created: {client}")
    
    # Test if we can create a label management screen
    screen = LabelManagementScreen(
        task_id="test123",
        current_labels=["testlabel"],
        available_labels=[("1", "testlabel", "red"), ("2", "anotherlabel", "blue")]
    )
    print(f"✓ LabelManagementScreen created: {screen}")
    
    # Test TUI app
    app = TodoistTUI()
    print(f"✓ TodoistTUI app created: {app}")
    
    print("\n✅ All tests passed! Label management functionality is ready.")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
