# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Fixed
- **API Integration**: Migrated from deprecated Todoist sync API to current REST API v1
- **Filter Display**: Fixed FilterSelectScreen not displaying user-defined Todoist filters
- **Error Handling**: Improved handling of deprecated API endpoints (410 Gone errors)

### Added  
- **Documentation**: Added comprehensive Todoist API v1 documentation references
- **Logging**: Enhanced debugging with detailed API interaction logging
- **API Validation**: Added proper filter fetching before displaying filter modal

### Technical Changes
- Updated all API calls to use https://api.todoist.com/rest/v1/ endpoints
- Added canonical API documentation reference: https://developer.todoist.com/api/v1/
- Improved error handling for API endpoint deprecation
- Enhanced filter caching and loading mechanisms

---

## Documentation

For API integration work, always refer to the **[Todoist API v1 Documentation](https://developer.todoist.com/api/v1/)** as the canonical, up-to-date reference.
