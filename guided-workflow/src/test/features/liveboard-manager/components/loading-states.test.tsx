import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { LibraryPane } from "~/features/liveboard-manager/components/LibraryPane";
import { WorkspacePane } from "~/features/liveboard-manager/components/WorkspacePane";
import type {
  ILibraryPaneProps,
  IWorkspacePaneProps,
} from "~/features/liveboard-manager/types";

describe("Loading States Tests", () => {
  const baseLibraryProps: ILibraryPaneProps = {
    state: {
      items: [],
      filteredItems: [],
      searchQuery: "",
      activeFilter: "all",
      isLoading: false,
    },
    onSearchChange: vi.fn(),
    onFilterChange: vi.fn(),
    onAddToWorkspace: vi.fn(),
    onCopy: vi.fn(),
    onDelete: vi.fn(),
  };

  const baseWorkspaceProps: IWorkspacePaneProps = {
    state: {
      items: [],
      isLoading: false,
      hasChanges: false,
    },
    canvasName: "Test Canvas",
    canvasId: "123",
    onRemoveFromWorkspace: vi.fn(),
    onRename: vi.fn(),
    onCopy: vi.fn(),
    onSaveAsTemplate: vi.fn(),
  };

  describe("LibraryPane Loading States", () => {
    it("should display LinearProgress when isLoading is true", () => {
      const loadingProps = {
        ...baseLibraryProps,
        state: {
          ...baseLibraryProps.state!,
          isLoading: true,
        },
      };

      render(<LibraryPane {...loadingProps} />);

      // Check for LinearProgress component
      const progressBar = document.querySelector(".MuiLinearProgress-root");
      expect(progressBar).toBeInTheDocument();
    });

    it("should not display LinearProgress when isLoading is false", () => {
      render(<LibraryPane {...baseLibraryProps} />);

      // Check that LinearProgress is not present
      const progressBar = document.querySelector(".MuiLinearProgress-root");
      expect(progressBar).not.toBeInTheDocument();
    });

    it("should display initial loading state when state is null", () => {
      const nullStateProps = {
        ...baseLibraryProps,
        state: null,
      };

      render(<LibraryPane {...nullStateProps} />);

      // Check for loading text
      expect(screen.getByText("Loading...")).toBeInTheDocument();

      // Verify header is still displayed
      expect(screen.getByText("Liveboard Library")).toBeInTheDocument();
    });

    it("should show proper loading indicator height and styling", () => {
      const loadingProps = {
        ...baseLibraryProps,
        state: {
          ...baseLibraryProps.state!,
          isLoading: true,
        },
      };

      render(<LibraryPane {...loadingProps} />);

      const progressBar = document.querySelector(".MuiLinearProgress-root");
      expect(progressBar).toHaveStyle({ height: "2px" });
    });

    it("should maintain functionality while loading", () => {
      const loadingProps = {
        ...baseLibraryProps,
        state: {
          ...baseLibraryProps.state!,
          isLoading: true,
          items: [
            {
              id: "1",
              display_name: "Test Item",
              category: "standard" as const,
              isInWorkspace: false,
            },
          ],
          filteredItems: [
            {
              id: "1",
              display_name: "Test Item",
              category: "standard" as const,
              isInWorkspace: false,
            },
          ],
        },
      };

      render(<LibraryPane {...loadingProps} />);

      // Verify content is still displayed during loading
      expect(screen.getByText("Test Item")).toBeInTheDocument();
      // Verify loading indicator is present
      const progressBar = document.querySelector(".MuiLinearProgress-root");
      expect(progressBar).toBeInTheDocument();
    });
  });

  describe("WorkspacePane Loading States", () => {
    it("should display LinearProgress when isLoading is true", () => {
      const loadingProps = {
        ...baseWorkspaceProps,
        state: {
          ...baseWorkspaceProps.state!,
          isLoading: true,
        },
      };

      render(<WorkspacePane {...loadingProps} />);

      // Check for LinearProgress component
      const progressBar = document.querySelector(".MuiLinearProgress-root");
      expect(progressBar).toBeInTheDocument();
    });

    it("should not display LinearProgress when isLoading is false", () => {
      render(<WorkspacePane {...baseWorkspaceProps} />);

      // Check that LinearProgress is not present
      const progressBar = document.querySelector(".MuiLinearProgress-root");
      expect(progressBar).not.toBeInTheDocument();
    });

    it("should display initial loading state when state is null", () => {
      const nullStateProps = {
        ...baseWorkspaceProps,
        state: null,
      };

      render(<WorkspacePane {...nullStateProps} />);

      // Check for loading text
      expect(screen.getByText("Loading...")).toBeInTheDocument();
      // Verify header is still displayed
      expect(screen.getByText("Active Workspace")).toBeInTheDocument();

      // Verify canvas info is displayed
      expect(screen.getByText("Canvas: Test Canvas (123)")).toBeInTheDocument();
    });

    it("should show proper loading indicator height and styling", () => {
      const loadingProps = {
        ...baseWorkspaceProps,
        state: {
          ...baseWorkspaceProps.state!,
          isLoading: true,
        },
      };

      render(<WorkspacePane {...loadingProps} />);

      const progressBar = document.querySelector(".MuiLinearProgress-root");
      expect(progressBar).toHaveStyle({ height: "2px" });
    });

    it("should maintain functionality while loading", () => {
      const loadingProps = {
        ...baseWorkspaceProps,
        state: {
          ...baseWorkspaceProps.state!,
          isLoading: true,
          items: [
            {
              id: "1",
              display_name: "Test Workspace Item",
              category: "standard" as const,
              isInWorkspace: true,
            },
          ],
        },
      };

      render(<WorkspacePane {...loadingProps} />);

      // Verify content is still displayed during loading
      expect(screen.getByText("Test Workspace Item")).toBeInTheDocument();

      // Verify loading indicator is present
      const progressBar = document.querySelector(".MuiLinearProgress-root");
      expect(progressBar).toBeInTheDocument();
    });

    it("should display loading state with canvas information preserved", () => {
      const nullStateProps = {
        ...baseWorkspaceProps,
        state: null,
        canvasName: "Production Canvas",
        canvasId: "prod-456",
      };

      render(<WorkspacePane {...nullStateProps} />);

      // Verify canvas information is preserved during loading
      expect(
        screen.getByText("Canvas: Production Canvas (prod-456)")
      ).toBeInTheDocument();
      expect(screen.getByText("Loading...")).toBeInTheDocument();
    });
  });

  describe("Loading State Transitions", () => {
    it("should properly transition from loading to loaded state in LibraryPane", () => {
      const { rerender } = render(
        <LibraryPane
          {...{
            ...baseLibraryProps,
            state: {
              ...baseLibraryProps.state!,
              isLoading: true,
            },
          }}
        />
      );

      // Verify loading state
      expect(
        document.querySelector(".MuiLinearProgress-root")
      ).toBeInTheDocument();

      // Transition to loaded state
      rerender(
        <LibraryPane
          {...{
            ...baseLibraryProps,
            state: {
              ...baseLibraryProps.state!,
              isLoading: false,
            },
          }}
        />
      );

      // Verify loading indicator is removed
      expect(
        document.querySelector(".MuiLinearProgress-root")
      ).not.toBeInTheDocument();
    });

    it("should properly transition from loading to loaded state in WorkspacePane", () => {
      const { rerender } = render(
        <WorkspacePane
          {...{
            ...baseWorkspaceProps,
            state: {
              ...baseWorkspaceProps.state!,
              isLoading: true,
            },
          }}
        />
      );

      // Verify loading state
      expect(
        document.querySelector(".MuiLinearProgress-root")
      ).toBeInTheDocument();

      // Transition to loaded state
      rerender(
        <WorkspacePane
          {...{
            ...baseWorkspaceProps,
            state: {
              ...baseWorkspaceProps.state!,
              isLoading: false,
            },
          }}
        />
      );

      // Verify loading indicator is removed
      expect(
        document.querySelector(".MuiLinearProgress-root")
      ).not.toBeInTheDocument();
    });
  });
});
