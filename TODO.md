# Todoist TUI - Feature Roadmap & TODO

## 🎯 **Current Status**
- ✅ **Completed**: Basic TUI with task CRUD operations
- ✅ **Completed**: Project filtering and management
- ✅ **Completed**: Label management with multi-select
- ✅ **Completed**: Natural language task parsing
- ✅ **Completed**: Vim-style navigation
- ✅ **Completed**: Refresh functionality
- ✅ **Completed**: Modular codebase architecture
- ✅ **Completed**: Todoist API v1 integration with current REST endpoints (deprecated sync API migrated)
- ✅ **Completed**: Filter display functionality with proper API v1 integration

---

## 🚀 **HIGH PRIORITY** (Phase 1 - Core Features)

### 1. Task Priorities & Visual Indicators
- [ ] **1.1** Add priority field to task display table
- [ ] **1.2** Implement priority setting in add/edit task modals
- [ ] **1.3** Add priority visual indicators (colors/symbols: P1🔴, P2🟡, P3🔵, P4⚪)
- [ ] **1.4** Add priority-based sorting option
- [ ] **1.5** Add `priority` keybinding to quickly set task priority

### 2. Due Date Management & Time-Based Filtering
- [ ] **2.1** Add due date time display (not just date)
- ✅ **2.2** Create filter menu modal (`f` key)
- ✅ **2.3** Implement "Today" filter (`f` → `t`)
- ✅ **2.4** Implement "This Week" filter (`f` → `w`)
- ✅ **2.5** Implement "Overdue" filter (`f` → `o`)
- ✅ **2.6** Add "All" filter to clear filters (`f` → `a`)
- [ ] **2.7** Add visual indicators for overdue tasks (red highlighting)
- [ ] **2.8** Add "upcoming" indicators (tasks due within 3 days)
- ✅ **2.9** Show current filter in status/title bar

### 3. Task Sorting & Organization
- [ ] **3.1** Add sort menu modal (`s` key)
- [ ] **3.2** Implement sort by priority
- [ ] **3.3** Implement sort by due date
- [ ] **3.4** Implement sort by creation date
- [ ] **3.5** Implement alphabetical sort
- [ ] **3.6** Remember last sort preference

### 4. Settings & Configuration System
- [ ] **4.1** Create settings modal screen (`ctrl+,` key)
- [ ] **4.2** Add API token configuration
- [ ] **4.3** Add theme selection (light/dark)
- [ ] **4.4** Add default project setting
- [ ] **4.5** Add auto-refresh interval setting
- [ ] **4.6** Save settings to config file

### 5. Help & User Experience
- [ ] **5.1** Create help modal (`?` key)
- [ ] **5.2** Add contextual help tooltips
- [ ] **5.3** Create first-time user onboarding
- [ ] **5.4** Add status bar with current filter/mode info
- [ ] **5.5** Improve error messages with actionable suggestions

---

## 🔧 **MEDIUM PRIORITY** (Phase 2 - Enhanced Features)

### 6. Advanced Search & Filtering
- [ ] **6.1** Implement global task search (`/` key in main view)
- [ ] **6.2** Add search by task content
- [ ] **6.3** Add search by labels
- [ ] **6.4** Add search by project
- [ ] **6.5** Implement combined filters (project + label + due date)
- ✅ **6.6** Add saved filter functionality (user-defined filters via Todoist API)

### 7. Task Comments & Rich Content
- [ ] **7.1** Add task comments viewing (`c` key)
- [ ] **7.2** Add comment creation/editing
- [ ] **7.3** Support basic markdown in task descriptions
- [ ] **7.4** Add task notes field
- [ ] **7.5** Display comment count in task list

### 8. Undo & Better Error Handling
- [ ] **8.1** Implement undo for task completion (`ctrl+z`)
- [ ] **8.2** Implement undo for task deletion
- [ ] **8.3** Implement undo for task moves
- [ ] **8.4** Add confirmation dialogs for destructive actions
- [ ] **8.5** Better API error handling with retry options

### 9. Bulk Operations
- [ ] **9.1** Add multi-select mode (`v` key)
- [ ] **9.2** Implement bulk task completion
- [ ] **9.3** Implement bulk task deletion
- [ ] **9.4** Implement bulk project changes
- [ ] **9.5** Implement bulk label management

### 10. Performance & Caching
- [ ] **10.1** Implement lazy loading for large task lists
- [ ] **10.2** Add background sync every N minutes
- [ ] **10.3** Optimize API calls with batching
- [ ] **10.4** Add loading indicators for slow operations
- [ ] **10.5** Implement local task caching with timestamps

---

## 🌟 **LOW PRIORITY** (Phase 3 - Advanced Features)

### 11. Task Templates & Productivity
- [ ] **11.1** Create task template system
- [ ] **11.2** Add common task templates (meeting, code review, etc.)
- [ ] **11.3** Implement task duplication (`ctrl+d`)
- [ ] **11.4** Add quick task creation from templates
- [ ] **11.5** Task auto-categorization based on content

### 12. Import/Export & Data Management
- [ ] **12.1** Export tasks to CSV
- [ ] **12.2** Export tasks to JSON
- [ ] **12.3** Export tasks to Markdown
- [ ] **12.4** Import tasks from CSV
- [ ] **12.5** Local backup functionality

### 13. Visual Enhancements
- [ ] **13.1** Add color-coded projects
- [ ] **13.2** Implement custom color themes
- [ ] **13.3** Add progress bars for project completion
- [ ] **13.4** Implement task grouping by project
- [ ] **13.5** Add calendar view for due dates

### 14. Recurring Tasks & Scheduling
- [ ] **14.1** Display recurring task patterns
- [ ] **14.2** Add recurring task creation (limited by API)
- [ ] **14.3** Show next occurrence dates
- [ ] **14.4** Handle recurring task completion properly

### 15. Collaboration Features
- [ ] **15.1** Display task assignees (if any)
- [ ] **15.2** Show shared project indicators
- [ ] **15.3** Display activity/collaboration history
- [ ] **15.4** Add @mention support in comments

---

## 🔨 **TECHNICAL DEBT & IMPROVEMENTS**

### 16. Code Quality & Architecture
- [ ] **16.1** Add comprehensive error logging
- [ ] **16.2** Implement proper unit tests
- [ ] **16.3** Add integration tests
- [ ] **16.4** Improve type hints throughout codebase
- [ ] **16.5** Add docstrings to all public methods

### 17. Configuration & Customization
- [ ] **17.1** Make keybindings customizable
- [ ] **17.2** Add configuration file validation
- [ ] **17.3** Implement configuration migration
- [ ] **17.4** Add environment variable support
- [ ] **17.5** Create config file documentation

### 18. Accessibility & Usability
- [ ] **18.1** Add screen reader support
- [ ] **18.2** Implement high contrast mode
- [ ] **18.3** Add font size options
- [ ] **18.4** Support colorblind-friendly indicators
- [ ] **18.5** Add keyboard-only navigation mode

---

## 📋 **IMPLEMENTATION NOTES**

### Quick Reference for Implementation:
```bash
# To work on a specific feature:
# 1. Create feature branch: git checkout -b feature/1.1-task-priorities
# 2. Implement feature following the numbered sub-tasks
# 3. Test thoroughly
# 4. Update this TODO with ✅ when complete
# 5. Commit and merge

# File structure for new features:
# - API changes: tuidoist/api/__init__.py
# - New screens: tuidoist/screens/__init__.py
# - App-level features: tuidoist/app.py
# - Utilities: tuidoist/utils/__init__.py
# - Styling: tuidoist/styles.tcss
```

### Priority Guidelines:
- **HIGH**: Essential features that significantly improve daily usage
- **MEDIUM**: Nice-to-have features that enhance user experience
- **LOW**: Advanced features for power users and edge cases

### Completion Tracking:
- Use `✅` for completed items
- Use `🚧` for items in progress
- Use `⚠️` for blocked items (add note why)
- Use `❌` for cancelled/rejected items

---

## 🎯 **NEXT ACTIONS**

**Immediate next steps (recommended order):**
1. Start with **1.1-1.5** (Task Priorities) - Foundation for better task management
2. Move to **2.1-2.6** (Due Date Management) - High user value
3. Implement **5.1-5.2** (Help System) - Improves discoverability
4. Add **3.1-3.6** (Task Sorting) - Essential for organization
5. Create **4.1-4.6** (Settings System) - Infrastructure for future features

**Estimated timeline:**
- Phase 1 (HIGH): 2-3 weeks
- Phase 2 (MEDIUM): 4-6 weeks  
- Phase 3 (LOW): 8-12 weeks

---

*Last updated: June 22, 2025*
*Total features: ~85 individual tasks across 18 categories*
