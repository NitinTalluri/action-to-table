import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { LibraryPane } from "~/features/liveboard-manager/components/LibraryPane";
import { WorkspacePane } from "~/features/liveboard-manager/components/WorkspacePane";
import type {
  ILibraryPaneProps,
  IWorkspacePaneProps,
} from "~/features/liveboard-manager/types";

describe("Header Cleanup Tests", () => {
  describe("LibraryPane Header", () => {
    const mockLibraryProps: ILibraryPaneProps = {
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

    it("should not contain emoji icons in the header text", () => {
      render(<LibraryPane {...mockLibraryProps} />);

      // Check that the header text does not contain emoji characters
      const headerElement = screen.getByText(/Liveboard Library/);
      expect(headerElement).toBeInTheDocument();

      // Verify no emoji characters (📚) are present
      expect(headerElement.textContent).not.toMatch(/📚/);
      expect(headerElement.textContent).toBe("Liveboard Library");
    });

    it("should display clean header text without decorative icons", () => {
      render(<LibraryPane {...mockLibraryProps} />);

      // Verify the header contains only text, no emoji decorations
      const headerElement = screen.getByText("Liveboard Library");
      expect(headerElement).toHaveTextContent("Liveboard Library");
      expect(headerElement.textContent).not.toContain("📚");
    });

    it("should maintain header functionality without emoji icons", () => {
      render(<LibraryPane {...mockLibraryProps} />);

      // Verify header is still properly structured
      const headerElement = screen.getByText("Liveboard Library");
      expect(headerElement).toBeInTheDocument();
      expect(headerElement.tagName).toBe("H6");
    });
  });

  describe("WorkspacePane Header", () => {
    const mockWorkspaceProps: IWorkspacePaneProps = {
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

    it("should not contain emoji icons in the header text", () => {
      render(<WorkspacePane {...mockWorkspaceProps} />);

      // Check that the header text does not contain emoji characters
      const headerElement = screen.getByText(/Active Workspace/);
      expect(headerElement).toBeInTheDocument();

      // Verify no emoji characters (🎯) are present
      expect(headerElement.textContent).not.toMatch(/🎯/);
      expect(headerElement.textContent).toBe("Active Workspace");
    });

    it("should display clean header text without decorative icons", () => {
      render(<WorkspacePane {...mockWorkspaceProps} />);

      // Verify the header contains only text, no emoji decorations
      const headerElement = screen.getByText("Active Workspace");
      expect(headerElement).toHaveTextContent("Active Workspace");
      expect(headerElement.textContent).not.toContain("🎯");
    });

    it("should maintain header functionality without emoji icons", () => {
      render(<WorkspacePane {...mockWorkspaceProps} />);

      // Verify header is still properly structured
      const headerElement = screen.getByText("Active Workspace");
      expect(headerElement).toBeInTheDocument();
      expect(headerElement.tagName).toBe("H6");
    });

    it("should preserve status chip functionality after header cleanup", () => {
      const propsWithChanges = {
        ...mockWorkspaceProps,
        state: {
          ...mockWorkspaceProps.state,
          hasChanges: true,
        },
      };

      render(<WorkspacePane {...propsWithChanges} />);

      // Verify status chip is still present and functional
      expect(screen.getByText("Unsaved changes")).toBeInTheDocument();

      // Verify header text is clean
      const headerElement = screen.getByText("Active Workspace");
      expect(headerElement.textContent).toBe("Active Workspace");
    });
  });

  describe("Loading State Headers", () => {
    it("should display clean LibraryPane header during loading state", () => {
      const mockProps: ILibraryPaneProps = {
        state: null, // This triggers loading state
        onSearchChange: vi.fn(),
        onFilterChange: vi.fn(),
        onAddToWorkspace: vi.fn(),
        onCopy: vi.fn(),
        onDelete: vi.fn(),
      };

      render(<LibraryPane {...mockProps} />);

      // Verify loading state header is clean
      const headerElement = screen.getByText("Liveboard Library");
      expect(headerElement.textContent).toBe("Liveboard Library");
      expect(headerElement.textContent).not.toContain("📚");
    });

    it("should display clean WorkspacePane header during loading state", () => {
      const mockProps: IWorkspacePaneProps = {
        state: null, // This triggers loading state
        canvasName: "Test Canvas",
        canvasId: "123",
        onRemoveFromWorkspace: vi.fn(),
        onRename: vi.fn(),
        onCopy: vi.fn(),
        onSaveAsTemplate: vi.fn(),
      };

      render(<WorkspacePane {...mockProps} />);

      // Verify loading state header is clean
      const headerElement = screen.getByText("Active Workspace");
      expect(headerElement.textContent).toBe("Active Workspace");
      expect(headerElement.textContent).not.toContain("🎯");
    });
  });
});
