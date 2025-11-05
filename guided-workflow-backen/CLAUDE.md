# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Commands

### Development

```bash
# Start the development server
npm run dev

# Build for production
npm run build

# Run linting before commits
npx lint-staged --allow-empty

# Testing
npm test                 # Run tests in interactive watch mode
npm run test:run         # Run tests once
npm run test:coverage    # Run tests with coverage
npm run test:ui          # Run tests with UI
npm run test:watch       # Run tests in watch mode

# Test specific features
npm test -- src/test/features/liveboard-manager  # Run all liveboard manager tests
npm test -- integration.test.tsx                 # Run integration tests

# Development setup
npm run prepare-dev      # Set up Husky git hooks
```

### Environment

The application supports three different environments:

- **Local Development**: Uses a .env.local file, runs on localhost:3000 with proxy to localhost:8080 for API
- **Development**: Uses Dev AWS Amplify, configured in buildspec.dev.yml
- **Production**: Uses Prod AWS Amplify, configured in buildspec.yml

### Docker

```bash
# Login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 837578041534.dkr.ecr.us-east-1.amazonaws.com

# Build Docker image
docker build . -t guided-workflow

# Run Docker container
docker run -p 3000:80 -d guided-workflow
```

## Architecture Overview

### Core Technologies

- **Frontend Framework**: React 18 with TypeScript
- **Build System**: Vite
- **Routing**: React Router v7
- **State Management**:
  - React Context for application-wide state
  - TanStack Query (React Query) for server state management
  - React Hooks for component state
- **UI Component Library**: Material UI v6
- **Styling**: SCSS modules and MUI's styled API
- **Authentication**: AWS Amplify/Cognito
- **API Communication**: Axios
- **Testing**: Vitest with React Testing Library

### Application Structure

The application follows a feature-based architecture:

```
src/
├── api/              # API service modules
├── app/              # Core application setup
├── components/       # Shared UI components
├── domain/           # Domain models and interfaces
├── features/         # Feature modules
│   ├── admin/
│   ├── announcements/
│   ├── canvas/
│   ├── ...
│   └── liveboard-manager/  # Currently being redesigned
├── hooks/            # Shared React hooks
├── queries/          # React Query definitions
├── router/           # Application routes
├── scss/             # Global styles
├── test/             # Test utilities and mocks
├── theme/            # MUI theme configuration
├── types/            # TypeScript type definitions
└── utils/            # Utility functions
```

### Key Features

1. **Liveboard Manager**: A two-pane interface for managing liveboards with library and workspace components (currently being redesigned)
2. **Tasks and Templates**: Views for managing tasks and templates, with tasks pulled from a queue based on value points
3. **Engagements**: Management of engagements throughout the application
4. **Time Tracking**: Features for tracking time spent on tasks
5. **Admin Functions**: Administrative features for users with appropriate permissions

### Data Flow

- Uses React Query for data fetching, caching, and state management
- API requests go through axios interceptors for authentication
- AWS Cognito provides authentication and user management
- ThoughtSpot integration for dashboard and analytics capabilities

### Environment Configuration

Environment variables are prefixed with `VITE_` for client-side access and are set during build time.

## Feature-specific Information

### Liveboard Manager

The liveboard manager (currently being redesigned) uses a two-pane layout:

- Left pane: Library of available liveboards (templates)
- Right pane: Workspace containing active liveboards for the current canvas

The component uses custom hooks like `useLiveboardManager` to track state and pending changes.

### Deployment Process

1. Feature branches are merged into the develop branch
2. Develop branch is merged into master when ready for production
3. CodeBuild builds the application using the appropriate buildspec
4. After building, the Kubernetes cluster requires manual deployment to update

## Development Patterns and Best Practices

### Context Discovery Strategy

When exploring unfamiliar features or trying to understand functionality:

1. **Look for README files first**: Always check for README.md files in feature directories as they contain high-level documentation and process flows
2. **Examine main component files**: Review index files and primary component implementations
3. **Check related API files**: Look at corresponding API service files for data flow understanding
4. **Review test files**: Tests often reveal expected behavior and edge cases

This approach ensures you get comprehensive context before diving into implementation details.

### Spec-Driven Development Workflow

The project uses a structured specification-driven development approach:

1. **Requirements Phase**: Document detailed requirements using EARS format (WHEN/THEN/IF statements)
2. **Design Phase**: Create technical design documents with clear architecture decisions
3. **Task Breakdown**: Decompose features into atomic, testable tasks (15-30 minutes each)
4. **Systematic Implementation**: Execute tasks with validation at each phase

### Schema-First Architecture

**Zod Schema Patterns**:

- Create dedicated schemas for new data models and compose using `.merge()` method
- Always infer TypeScript types from schemas rather than defining them separately
- Extend existing schemas rather than duplicating field definitions (e.g., ManagerPortalClaimedBookingSchema extends ManagerPortalUnclaimedBookingSchema)
- Use nullable fields appropriately for optional data
- For API request/response schemas, create separate validation schemas (e.g., ModifyBookingCurrentSalesLevel)
- Use `.nullish()` for fields that can be null, undefined, or missing
- Parse JSON strings within schemas when dealing with complex nested data structures

### Testing Strategy

**Comprehensive Coverage**:

- Unit tests for individual component behavior using Vitest + React Testing Library
- Integration tests for multi-component workflows in `src/test/features/`
- Mock external dependencies consistently (sonner, React Query, custom hooks)
- Focus on user behavior and interactions rather than implementation details

**Test Organization**:

- Co-locate unit tests with components (`ComponentName.test.tsx`)
- Use proper TypeScript typing for all mock data and test scenarios
- Test error states, edge cases, and various data conditions

### React Query Integration Patterns

**Optimistic Updates**:

- Use `onMutate` callback to immediately update cache with expected results
- Parse complex data from lookup tables during optimistic updates (JSON.parse)
- Always invalidate queries in `onSettled` to ensure data consistency
- Provide immediate user feedback while maintaining data integrity
- Handle nested data structures properly in optimistic update transformations

### Component Integration Patterns

**Feature Module Organization**:

- Place new components within existing feature directories (e.g., `current-sales-level/` within `dc-types-form/`)
- Use index.ts files for clean public APIs and consistent exports
- Follow established import patterns and maintain alphabetical ordering
- Create sub-directories for complex features with multiple related components

**Dialog and Modal Patterns**:

- Separate dialog content into distinct components for better testability
- Use DialogCloseButton component for consistent close button styling
- Implement proper loading states and disable controls during pending operations
- Provide clear save/cancel actions with proper validation states

**UI Consistency**:

- Reuse existing components (ReadOnlyChip, IconButton patterns) for visual consistency
- Maintain consistent container structures and styling approaches
- Update terminology across all related files when making label changes
- Separate related but distinct components into individual rows/containers for improved visual hierarchy
- Use Material-UI Box components with consistent spacing (`paddingBottom: 1, gap: 0.5`) for layout uniformity
- For data display, use grid layouts with auto-fill columns (`gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))"`)
- Display missing data consistently with "--" rather than "N/A" for better visual consistency

### Development Quality Practices

**Type Safety**:

- Maintain strict TypeScript configuration
- Use proper interfaces for all component props and function parameters
- Leverage Zod for runtime validation and type inference

**Code Reuse**:

- Identify and leverage existing patterns before creating new implementations
- Use established component libraries and styling approaches
- Follow existing error handling and user feedback patterns (toast notifications)

**Performance Considerations**:

- Run `npm run build` to verify no type errors or build issues
- Test components with various data states and edge cases
- Ensure responsive design works across different viewport sizes
- The dist folder has been removed to maintain a clean development workspace

### Code Quality and Git Workflow

**Linting and Pre-commit Workflow**:

- Always run `npx lint-staged --allow-empty` after `git add` to ensure code quality
- Fix ESLint errors by replacing `any` types with proper TypeScript interfaces
- Use import sorting and formatting rules consistently across all files
- Add missing button types (`type="button"`) for accessibility compliance
- Remove unused imports to keep code clean and maintainable
- Husky pre-commit hook automatically runs lint-staged on commit

**ESLint Configuration**:
- TypeScript strict mode enabled (`@typescript-eslint/no-explicit-any`: `error`)
- React hooks and refresh plugins configured
- TanStack Query exhaustive deps checking enabled
- Simple import sorting enforced
- Unused variables flagged as warnings

**Commit Strategy**:

- **ALWAYS update CHANGELOG.md before committing** - Document all significant changes in the [Unreleased] section
- Use descriptive commit messages following conventional commit format (`feat:`, `fix:`, etc.)
- Do not include author attribution in commit messages unless explicitly requested
- Use HEREDOC syntax (`cat <<'EOF'`) for multi-line commit messages to avoid shell escaping
- Include bullet points summarizing key changes and their impact
- Run lint-staged before every commit to maintain consistent code quality

**CHANGELOG Update Requirements**:
- Add new features to the "### Added" section with detailed bullet points
- Document API changes, schema updates, and component modifications in "### Changed"
- Include bug fixes in "### Fixed" section
- Provide context on integration points, dependencies, and architectural decisions
- Use specific component names and file paths for easy reference

## Migration from TmlHandlerDialog to LiveboardManager

When replacing the legacy TmlHandlerDialog with the new LiveboardManager:

1. Update imports: Replace `TmlHandlerDialog` with `LiveboardManager` from `~/features/liveboard-manager`
2. All existing props are compatible - no changes needed to parent components
3. Benefits include improved UX with two-pane layout, better accessibility, and enhanced search/filtering
