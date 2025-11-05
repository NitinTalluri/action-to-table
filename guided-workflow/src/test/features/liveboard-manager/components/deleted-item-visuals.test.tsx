import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { LiveboardItem } from "~/features/liveboard-manager/components/LiveboardItem";
import type { ILiveboardItemProps } from "~/features/liveboard-manager/types";

describe("Deleted Item Visual Indicators Tests", () => {
  const baseMockItem = {
    id: "1",
    display_name: "Test Liveboard",
    category: "standard" as const,
    isInWorkspace: false,
  };

  const baseMockActions = {
    onAddToWorkspace: vi.fn(),
    onRemoveFromWorkspace: vi.fn(),
    onRename: vi.fn(),
    onCopy: vi.fn(),
    onDelete: vi.fn(),
    onSaveAsTemplate: vi.fn(),
  };

  describe("Deleted Item Styling", () => {
    it("should apply reduced opacity to deleted items", () => {
      const deletedItem = {
        ...baseMockItem,
        isDeleted: true,
      };

      const props: ILiveboardItemProps = {
        item: deletedItem,
        variant: "library",
        actions: baseMockActions,
      };

      render(<LiveboardItem {...props} />);

      // Check for reduced opacity styling on the container
      const itemContainer = screen.getByTestId("liveboard-item-container");
      expect(itemContainer).toHaveStyle({ opacity: "0.6" });
    });

    it("should apply strikethrough text decoration to deleted items", () => {
      const deletedItem = {
        ...baseMockItem,
        isDeleted: true,
      };

      const props: ILiveboardItemProps = {
        item: deletedItem,
        variant: "library",
        actions: baseMockActions,
      };

      render(<LiveboardItem {...props} />);

      // Check for strikethrough text decoration
      const itemTitle = screen.getByText("Test Liveboard");
      expect(itemTitle).toHaveStyle({ textDecoration: "line-through" });
    });

    it('should display "Deleted" chip for deleted items', () => {
      const deletedItem = {
        ...baseMockItem,
        isDeleted: true,
      };

      const props: ILiveboardItemProps = {
        item: deletedItem,
        variant: "library",
        actions: baseMockActions,
      };

      render(<LiveboardItem {...props} />);

      // Check for deleted chip
      expect(screen.getByText("Deleted")).toBeInTheDocument();

      // Verify chip styling
      const deletedChip = screen.getByText("Deleted").closest(".MuiChip-root");
      expect(deletedChip).toHaveClass("MuiChip-colorError");
    });

    it("should not apply deleted styling to non-deleted items", () => {
      const normalItem = {
        ...baseMockItem,
        isDeleted: false,
      };

      const props: ILiveboardItemProps = {
        item: normalItem,
        variant: "library",
        actions: baseMockActions,
      };

      render(<LiveboardItem {...props} />);

      // Verify normal styling
      const itemContainer = screen.getByTestId("liveboard-item-container");
      expect(itemContainer).not.toHaveStyle({ opacity: "0.6" });

      const itemTitle = screen.getByText("Test Liveboard");
      expect(itemTitle).not.toHaveStyle({ textDecoration: "line-through" });

      // Verify no deleted chip
      expect(screen.queryByText("Deleted")).not.toBeInTheDocument();
    });

    it("should handle undefined isDeleted property as non-deleted", () => {
      const itemWithoutDeletedFlag = {
        ...baseMockItem,
        // isDeleted is undefined
      };

      const props: ILiveboardItemProps = {
        item: itemWithoutDeletedFlag,
        variant: "library",
        actions: baseMockActions,
      };

      render(<LiveboardItem {...props} />);

      // Should behave as non-deleted item
      const itemContainer = screen.getByTestId("liveboard-item-container");
      expect(itemContainer).not.toHaveStyle({ opacity: "0.6" });

      const itemTitle = screen.getByText("Test Liveboard");
      expect(itemTitle).not.toHaveStyle({ textDecoration: "line-through" });

      expect(screen.queryByText("Deleted")).not.toBeInTheDocument();
    });
  });

  describe("Deleted Item Interactions", () => {
    it("should disable actions for deleted items", () => {
      const deletedItem = {
        ...baseMockItem,
        isDeleted: true,
      };

      const props: ILiveboardItemProps = {
        item: deletedItem,
        variant: "library",
        actions: baseMockActions,
      };

      render(<LiveboardItem {...props} />);

      // Check that primary action button is disabled
      const addButton = screen.getByRole("button", { name: /Add/ });
      expect(addButton).toBeDisabled();
    });

    it("should disable menu actions for deleted items", () => {
      const deletedItem = {
        ...baseMockItem,
        isDeleted: true,
      };

      const props: ILiveboardItemProps = {
        item: deletedItem,
        variant: "workspace",
        actions: baseMockActions,
      };

      render(<LiveboardItem {...props} />);

      // Check that more actions button (with MoreVertIcon) is disabled
      const moreButtons = screen.getAllByTitle("This item has been deleted");
      const moreButton = moreButtons.find((button) =>
        button.querySelector('[data-testid="MoreVertIcon"]')
      );
      expect(moreButton).toBeDisabled();
    });

    it("should show tooltip explaining disabled state for deleted items", () => {
      const deletedItem = {
        ...baseMockItem,
        isDeleted: true,
      };

      const props: ILiveboardItemProps = {
        item: deletedItem,
        variant: "library",
        actions: baseMockActions,
      };

      render(<LiveboardItem {...props} />);

      // Check for tooltip or title attribute
      const addButton = screen.getByRole("button", { name: /Add/ });
      expect(addButton).toHaveAttribute("title", "This item has been deleted");
    });
  });

  describe("Deleted Item in Different Variants", () => {
    it("should apply deleted styling in library variant", () => {
      const deletedItem = {
        ...baseMockItem,
        isDeleted: true,
      };

      const props: ILiveboardItemProps = {
        item: deletedItem,
        variant: "library",
        actions: baseMockActions,
      };

      render(<LiveboardItem {...props} />);

      expect(screen.getByText("Deleted")).toBeInTheDocument();

      const itemTitle = screen.getByText("Test Liveboard");
      expect(itemTitle).toHaveStyle({ textDecoration: "line-through" });
    });

    it("should apply deleted styling in workspace variant", () => {
      const deletedItem = {
        ...baseMockItem,
        isDeleted: true,
        isInWorkspace: true,
      };

      const props: ILiveboardItemProps = {
        item: deletedItem,
        variant: "workspace",
        actions: baseMockActions,
      };

      render(<LiveboardItem {...props} />);

      expect(screen.getByText("Deleted")).toBeInTheDocument();

      const itemTitle = screen.getByText("Test Liveboard");
      expect(itemTitle).toHaveStyle({ textDecoration: "line-through" });
    });
  });

  describe("Deleted Item with Other Status Chips", () => {
    it('should display both "In Workspace" and "Deleted" chips when applicable', () => {
      const deletedWorkspaceItem = {
        ...baseMockItem,
        isDeleted: true,
        isInWorkspace: true,
      };

      const props: ILiveboardItemProps = {
        item: deletedWorkspaceItem,
        variant: "library",
        actions: baseMockActions,
      };

      render(<LiveboardItem {...props} />);

      // Both chips should be present
      expect(screen.getByText("In Workspace")).toBeInTheDocument();
      expect(screen.getByText("Deleted")).toBeInTheDocument();
    });

    it("should display category chip alongside deleted chip", () => {
      const deletedEngagementItem = {
        ...baseMockItem,
        isDeleted: true,
        category: "engagement" as const,
      };

      const props: ILiveboardItemProps = {
        item: deletedEngagementItem,
        variant: "library",
        actions: baseMockActions,
      };

      render(<LiveboardItem {...props} />);

      // Both category and deleted chips should be present
      expect(screen.getByText("Engagement")).toBeInTheDocument();
      expect(screen.getByText("Deleted")).toBeInTheDocument();
    });
  });

  describe("Deleted Item Accessibility", () => {
    it("should provide proper ARIA labels for deleted items", () => {
      const deletedItem = {
        ...baseMockItem,
        isDeleted: true,
      };

      const props: ILiveboardItemProps = {
        item: deletedItem,
        variant: "library",
        actions: baseMockActions,
      };

      render(<LiveboardItem {...props} />);

      // Check for aria-label indicating deleted state
      const itemContainer = screen.getByTestId("liveboard-item-container");
      expect(itemContainer).toHaveAttribute(
        "aria-label",
        expect.stringContaining("deleted")
      );
    });

    it("should maintain keyboard navigation for deleted items", () => {
      const deletedItem = {
        ...baseMockItem,
        isDeleted: true,
      };

      const props: ILiveboardItemProps = {
        item: deletedItem,
        variant: "library",
        actions: baseMockActions,
      };

      render(<LiveboardItem {...props} />);

      // Verify item container is still accessible
      const itemContainer = screen.getByTestId("liveboard-item-container");
      expect(itemContainer).toBeInTheDocument();

      // The container itself doesn't need to be focusable, but the buttons inside should be
      // (even if disabled, they should still be in the tab order for screen readers)
      const addButton = screen.getByRole("button", { name: /Add/ });
      expect(addButton).toBeInTheDocument();
    });
  });
});
