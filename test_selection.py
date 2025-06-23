#!/usr/bin/env python3
"""Test script to understand SelectionList widget capabilities"""

from textual.app import App, ComposeResult
from textual.widgets import SelectionList, Input, Static
from textual.widgets.selection_list import Selection
from textual.containers import Vertical
from textual.binding import Binding


class TestSelectionApp(App):
    """Test app for SelectionList widget"""
    
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("enter", "apply_selection", "Apply Selection"),
    ]
    
    def compose(self) -> ComposeResult:
        """Compose the UI"""
        # Sample labels
        labels = ["work", "personal", "urgent", "home", "shopping", "health", "project-a", "project-b"]
        
        # Create selections
        selections = [
            Selection(label, label, initial_state=False)
            for label in labels
        ]
        
        yield Static("Filter labels:", id="filter-label")
        yield Input(placeholder="Type to filter...", id="filter-input")
        yield Static("Select labels:", id="selection-label")
        yield SelectionList(*selections, id="selection-list")
        yield Static("Selected: None", id="selected-display")
    
    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle filter input changes"""
        if event.input.id == "filter-input":
            self.filter_selections(event.value)
    
    def filter_selections(self, filter_text: str) -> None:
        """Filter the selection list based on input"""
        selection_list = self.query_one("#selection-list", SelectionList)
        
        # Get all available labels
        all_labels = ["work", "personal", "urgent", "home", "shopping", "health", "project-a", "project-b"]
        
        # Filter labels
        if filter_text:
            filtered_labels = [label for label in all_labels if filter_text.lower() in label.lower()]
        else:
            filtered_labels = all_labels
        
        # Clear and repopulate
        selection_list.clear_options()
        for label in filtered_labels:
            selection_list.add_option(Selection(label, label, initial_state=False))
    
    def on_selection_list_selected_changed(self, event: SelectionList.SelectedChanged) -> None:
        """Handle selection changes"""
        selected_display = self.query_one("#selected-display", Static)
        selected_items = [selection.value for selection in event.selection_list.selected]
        selected_display.update(f"Selected: {', '.join(selected_items) if selected_items else 'None'}")
    
    def action_apply_selection(self) -> None:
        """Apply the current selection"""
        selection_list = self.query_one("#selection-list", SelectionList)
        selected_items = [selection.value for selection in selection_list.selected]
        self.exit(selected_items)


if __name__ == "__main__":
    app = TestSelectionApp()
    result = app.run()
    print(f"Selected labels: {result}")
