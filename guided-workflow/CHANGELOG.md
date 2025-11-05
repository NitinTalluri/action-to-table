# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [15.1.1] - 2025-10-14

### Fixed

- **HOTFIX**: Liveboard Manager copy operation ID generation and parent-child tracking
  - Changed `fileId` generation for copied items from `${item.fileId}_copy_${Date.now()}` to `-${Date.now()}` for consistency with prospecting booking pattern
  - Fixed duplicate `id` generation that was incorrectly using `fileId` as base instead of `id`
  - Added `parent_id` matching when marking library items after workspace removal
  - Ensures proper tracking of copied item lineage and prevents ID conflicts
  - Improved UI state consistency when removing copied items from workspace

## [15.1.0] - 2025-09-24

### Added

- SDP completion due_date integration for CXEA Scale collision resolution
  - Include due_date in completion requests to distinguish deliverables with same cycle_iterator
  - Enhanced optimistic updates to match tasks by due_date for accurate UI feedback
  - Updated TypeScript schemas to require due_date field in completion payloads

### Fixed

- Time tracking EditableCell user experience improvements
  - Add onWheel event handler to blur input on scroll preventing accidental value changes
  - Improve user interaction when scrolling over numeric input fields
  - Remove trailing commas for consistent code formatting
- Claim booking route step navigation timing issue
  - Fix isRenewal state update causing step skipping in the stepper workflow
  - Add parameterized getStepIndex function to calculate steps based on intended state
  - Update confirmRenewal and confirmNew functions to use explicit renewal state for step calculation
  - Ensure proper step transitions when switching between renewal and new booking types
  - Prevent React's asynchronous state updates from causing navigation inconsistencies

### Added

- CXEA Scale filtering toggle for unclaimed bookings table
  - Add toggle switch to show CXEA Scale bookings exclusively or exclude them (default)
  - Implement useBuyingProgramTableTypes hook integration for CXEA Scale identification
  - Add filtered data memoization for optimal performance with large booking datasets
  - Include Material-UI Switch component with proper labeling and responsive layout
  - Default behavior excludes CXEA Scale bookings to streamline standard workflow
  - Toggle allows managers to focus specifically on CXEA Scale bookings when needed

### Added

- Default engagement auto-selection for claim booking workflow
  - Add dc_engagement_id_default field to ManagerPortalUnclaimedBookingSchema
  - Implement automatic selection of default engagement when booking data loads
  - Add useEffect-based auto-selection logic to prevent render loops
  - Update claim booking route README with comprehensive auto-selection documentation
  - Streamline user experience by pre-selecting existing engagement assignments
- Sprint Goals admin route with HTML content embedding
  - Add new SprintGoalsRoute component at /support/admin/sprint-goals
  - Implement API integration with /api/v2/static/html endpoint for presigned URL retrieval
  - Create comprehensive React Query integration with proper caching (24-hour staleTime)
  - Add SprintGoalsResponseSchema with url and expires_secs validation using Zod
  - Embed HTML content directly in iframe using presigned URL for optimal performance
  - Include proper loading states, error handling, and responsive 70vh iframe layout
  - Add refetchOnMount: false to prevent unnecessary API calls on navigation
  - Integrate with existing support routes and admin permissions structure
- Canvas auto-enable for ThoughtSpot: Automatically enable disabled canvases when clicking ThoughtSpot chips, with loading state and proper 200/304 status handling
- Current Sales Level management system for claimed bookings
  - Add CurrentSalesDetailsRow component with complete CRUD operations for sales level data
  - Implement CurrentSalesDisplayGrid showing Sales Level 1-4 and Current Segment with grid layout
  - Add CurrentSalesEditDialog with searchable, filterable table for sales level selection
  - Create comprehensive API integration with updateCurrentSalesDetails endpoint
  - Support conditional edit functionality based on booking disengagement status
  - Include optimistic updates using React Query for immediate UI feedback
  - Add proper TypeScript schema validation using Zod for sales level data structures
  - Integrate seamlessly with existing DC Types form in claimed booking interface
  - Handle missing data gracefully with "--" display for null/undefined values
  - Implement sales level ID tracking and proper state management for editing workflows
- Comprehensive technical documentation for system architecture
  - Add README.md for Current Sales Level feature with complete technical specifications
  - Add README.md for DCTypes system with architecture overview and integration patterns
  - Include data flow diagrams, schema patterns, and performance optimization guidance
  - Document 20+ specialized hooks and lookup table usage patterns
  - Provide maintenance guidelines and extension patterns for future development
- Default Engagement column to claimed bookings table
  - Display engagement names with loading states using LinearProgress
  - Add filtering and sorting capabilities for engagement selection
  - Integrate with manager portal available engagements query
  - Support multi-select filtering for engagement filtering options
- Liveboard Manager redesign with library + workspace two-pane layout
  - Replace complex 3-column drag-and-drop interface with intuitive two-pane design
  - Add comprehensive TypeScript types and React components using Material-UI
  - Implement search, filtering, and workspace management functionality
  - Add visual status indicators with category and state chips
  - Improve state management with proper action tracking
- Context Discovery Strategy documentation in CLAUDE.md
  - Prioritize README files first when exploring unfamiliar features
  - Establish systematic approach: README → components → API → tests
  - Ensure comprehensive context before diving into implementation details
  - Add detailed documentation with architecture overview and usage guidelines
  - Include comprehensive test suite with specialized test files
  - Add SCSS modules for consistent styling
  - Improve accessibility with button-based interactions
  - Enhance with animation effects and scroll-to behavior for new items
  - Add special handling for newly created canvases with URL parameter tracking
  - Improve user feedback with comprehensive toast notifications
  - Implement clear workspace functionality with unified state tracking
  - Update documentation with expanded technical details and troubleshooting

### Changed

- Enhanced Manager Portal data models and API integration
  - Add sales level fields (sales_level_id, node_level1-4, node_segment) to TManagerPortalClaimedBooking schema
  - Extend ModifyBookingCurrentSalesLevel schema for sales level updates
  - Add TSalesLevel domain type with comprehensive Zod validation
  - Include updateCurrentSalesDetails API function with proper error handling
  - Add useSalesLevelTableTypes hook for accessing sales level lookup data
  - Integrate CurrentSalesDetailsRow into claimed booking workflow and exports
- Vendor CAM Assignment deliverable selection behavior
  - Remove automatic selection of deliverables based on existing CAM assignments (sdp_assigned_user_ids)
  - Implement clean slate approach where users must explicitly select all desired deliverables
  - Preserve navigation state restoration when moving between wizard steps
  - Update documentation to reflect new selection behavior and improved user control
  - Maintain cascading selection logic and hierarchical deliverable structure
- Update booking sales level terminology from "Booked Sav" to "Booked SL" for consistency
  - Update DcTypesForm labels for Booked SL 1, 2, and 3 display
  - Update booking details view labels to match new terminology
  - Maintain existing data field names while updating display labels
- Update .gitignore to exclude Claude Code configuration files (.claude directory)
- Enhanced tagging UX with Material-UI improvements
  - Update TaggedContainer to display tags in "TagsetName: TagName" format
  - Implement tag toggle functionality for selection/deselection
  - Enhance header styling with consistent typography and borders
  - Add green check icons to TagsetAccordion for clearer selection indicators
  - Refactor Tagging components for more consistent state management
  - Improve performance by filtering out empty tagsets
  - Fix accordion spacing issues with stable layout

### Fixed

- Correct TaggedContainer organization with TagsetName: TagName format
- Implement proper tag toggle functionality using parent handleTagRemove component

## [15.0.4] - 2025-08-15

### Maintenance

- Updated dependencies with security fixes
- Package maintenance updates

## [15.0.3] - 2025-08-01

### Fixed

- Fix MACD Historical Upload - Add Effective Date component and functionality

## [15.0.2] - 2025-07-25

### Fixed

- Fix engagement booking contract - Extended Status and Extended End Date
- Apply hotfix for time tracking and Canvas Snapshots

## [15.0.1] - 2025-07-20

### Fixed

- Fix wording change - snapshots 100 days

### Added

- Only send updated entries for Time Tracking (performance improvement)

## [15.0.0] - 2025-07-15

### Added

- Enable Bulk Serial Tagging functionality
- Allow skip data entry in MACD Audit
- MACD historical upload API Integration
- Update default engagement for claimed bookings
- Vendor drawer changes and update CAMS form
- Tag History for large data grids
- MACD Audit date range selection
- MACD handling multi-schemas
- React Route RBAC changes
- Instance & Serial Tagging for large data grids
- SEA File Upload improvements
- Bulk Tagging functionality
- Collector and Customer File upload improvements

### Changed

- Update Node.js version to 20
- Migrate to React Query for data management
- Allow Log Sign Off workflow for extended bookings
- Improve performance for Tag, Untag, and Extract operations
- Add presentation mode for ThoughtSpot
- Switch to external store for row data (improved performance)
- Enhanced error handling and success notifications

### Fixed

- Time-tracking update for entry_id
- Refetch Tag & Extract answer on mount
- Enable parsing dates as UTC (ignoring locale)
- Fix issue regarding setting state in render
- Vendor tab only show CXEA - Scale bookings
- Updated bookings while updating CAMS
- TypeScript error fixes
- Form schema update to facilitate primary CAM
- Claim-all pool-manager invalidate bookings query
- Bulk Tagging success modal
- Adjust WorkflowPage styles to prevent drawer from shrinking
- Update instance tagging payload structure
- MACD & SEA huge data upload issues

## [14.1.2] - 2025-06-25

### Fixed

- Fix TimeTracking grouping changes for engagement_id & week_num_in_year

## [14.1.1] - 2025-06-20

### Fixed

- Fix cross-charge booking form - submit button was not triggering 'submit' as it was outside the HTML form tag

## [14.1.0] - 2025-06-15

### Fixed

- Fix issues related to "Time Tracking" and Authentication (DC-479)
