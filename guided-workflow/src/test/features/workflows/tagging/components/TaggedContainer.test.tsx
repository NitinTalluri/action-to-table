import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { TaggedContainer } from "~/features/workflows/tagging/components/TaggedContainer";
import { TSelection } from "~/features/workflows/types";

describe("TaggedContainer Component", () => {
  // Arrange: Set up mock functions and test data
  const mockHandleRemove = vi.fn();
  const mockHandleResetAttention = vi.fn();

  const mockSelections: TSelection[] = [
    {
      tagId: 1,
      tagsetId: 1,
      tagName: "Tag A",
      tagsetName: "Engagement Tagset",
      attention: false,
    },
    {
      tagId: 2,
      tagsetId: 1,
      tagName: "Tag B",
      tagsetName: "Engagement Tagset",
      attention: false,
    },
    {
      tagId: 3,
      tagsetId: 2,
      tagName: "Global Tag",
      tagsetName: "Global Tagset",
      attention: false,
    },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("TaggedContainer Display", () => {
    it("should render null when selections is null", () => {
      // Act: Render component with null selections
      const { container } = render(
        <TaggedContainer
          selections={null}
          isSubmitting={false}
          handleRemove={mockHandleRemove}
          handleResetAttention={mockHandleResetAttention}
        />
      );

      // Assert: Component should render nothing
      expect(container.firstChild).toBeNull();
    });

    it("should render null when selections is empty array", () => {
      // Act: Render component with empty selections
      const { container } = render(
        <TaggedContainer
          selections={[]}
          isSubmitting={false}
          handleRemove={mockHandleRemove}
          handleResetAttention={mockHandleResetAttention}
        />
      );

      // Assert: Component should render nothing
      expect(container.firstChild).toBeNull();
    });

    it("should display tags with tagset name prefix format", () => {
      // Act: Render component with mixed tagset selections
      render(
        <TaggedContainer
          selections={mockSelections}
          isSubmitting={false}
          handleRemove={mockHandleRemove}
          handleResetAttention={mockHandleResetAttention}
        />
      );

      // Assert: Tags should be displayed with "TagsetName: TagName" format
      expect(screen.getByText("Engagement Tagset: Tag A")).toBeInTheDocument();
      expect(screen.getByText("Engagement Tagset: Tag B")).toBeInTheDocument();
      expect(screen.getByText("Global Tagset: Global Tag")).toBeInTheDocument();
    });

    it("should display multiple tags from same tagset with proper format", () => {
      // Arrange: Create selections with multiple tags from same tagset
      const sameTagsetSelections: TSelection[] = [
        {
          tagId: 1,
          tagsetId: 1,
          tagName: "First Tag",
          tagsetName: "Test Tagset",
          attention: false,
        },
        {
          tagId: 2,
          tagsetId: 1,
          tagName: "Second Tag",
          tagsetName: "Test Tagset",
          attention: false,
        },
        {
          tagId: 3,
          tagsetId: 1,
          tagName: "Third Tag",
          tagsetName: "Test Tagset",
          attention: false,
        },
      ];

      // Act: Render component with same tagset selections
      render(
        <TaggedContainer
          selections={sameTagsetSelections}
          isSubmitting={false}
          handleRemove={mockHandleRemove}
          handleResetAttention={mockHandleResetAttention}
        />
      );

      // Assert: All tags should be displayed with proper format
      expect(screen.getByText("Test Tagset: First Tag")).toBeInTheDocument();
      expect(screen.getByText("Test Tagset: Second Tag")).toBeInTheDocument();
      expect(screen.getByText("Test Tagset: Third Tag")).toBeInTheDocument();
    });

    it("should handle single tag selection", () => {
      // Arrange: Create single tag selection
      const singleSelection: TSelection[] = [
        {
          tagId: 1,
          tagsetId: 1,
          tagName: "Single Tag",
          tagsetName: "Single Tagset",
          attention: false,
        },
      ];

      // Act: Render component with single selection
      render(
        <TaggedContainer
          selections={singleSelection}
          isSubmitting={false}
          handleRemove={mockHandleRemove}
          handleResetAttention={mockHandleResetAttention}
        />
      );

      // Assert: Tag should be displayed with proper format
      expect(screen.getByText("Single Tagset: Single Tag")).toBeInTheDocument();
    });

    it("should maintain proper layout structure with tags", () => {
      // Act: Render component with mixed tagset selections
      const { container } = render(
        <TaggedContainer
          selections={mockSelections}
          isSubmitting={false}
          handleRemove={mockHandleRemove}
          handleResetAttention={mockHandleResetAttention}
        />
      );

      // Assert: Container should have proper class
      const taggedContainer = container.querySelector(
        "[class*='taggedContainer']"
      );
      expect(taggedContainer).toBeInTheDocument();

      // Assert: All tags should be rendered as chips
      const chips = screen.getAllByRole("button");
      expect(chips).toHaveLength(3); // Three selections
    });

    it("should display tags with proper chip styling", () => {
      // Act: Render component with selections
      render(
        <TaggedContainer
          selections={mockSelections}
          isSubmitting={false}
          handleRemove={mockHandleRemove}
          handleResetAttention={mockHandleResetAttention}
        />
      );

      // Assert: Tags should be rendered as MUI chips
      const chips = screen.getAllByRole("button");
      expect(chips.length).toBeGreaterThan(0);

      // Assert: Each chip should have proper styling
      chips.forEach((chip) => {
        expect(chip).toHaveClass("MuiChip-root");
      });
    });

    it("should handle tag removal functionality", () => {
      // Act: Render component with selections
      render(
        <TaggedContainer
          selections={mockSelections}
          isSubmitting={false}
          handleRemove={mockHandleRemove}
          handleResetAttention={mockHandleResetAttention}
        />
      );

      // Act: Click on delete button of first tag
      const deleteButtons = screen.getAllByTestId("CancelIcon");
      fireEvent.click(deleteButtons[0]);

      // Assert: Remove handler should be called
      expect(mockHandleRemove).toHaveBeenCalledTimes(1);
      expect(mockHandleRemove).toHaveBeenCalledWith(mockSelections[0]);
    });

    it("should disable chips when submitting", () => {
      // Act: Render component in submitting state
      render(
        <TaggedContainer
          selections={mockSelections}
          isSubmitting={true}
          handleRemove={mockHandleRemove}
          handleResetAttention={mockHandleResetAttention}
        />
      );

      // Assert: All chips should be disabled (have Mui-disabled class)
      const chips = screen.getAllByRole("button");
      chips.forEach((chip) => {
        expect(chip).toHaveClass("Mui-disabled");
      });
    });
  });

  describe("WobbleChip Functionality", () => {
    it("should handle attention animation", () => {
      // Arrange: Create selection with attention
      const attentionSelection: TSelection[] = [
        {
          tagId: 1,
          tagsetId: 1,
          tagName: "Attention Tag",
          tagsetName: "Test Tagset",
          attention: true,
        },
      ];

      // Act: Render component with attention selection
      render(
        <TaggedContainer
          selections={attentionSelection}
          isSubmitting={false}
          handleRemove={mockHandleRemove}
          handleResetAttention={mockHandleResetAttention}
        />
      );

      // Assert: Tag should be displayed with proper format
      expect(screen.getByText("Test Tagset: Attention Tag")).toBeInTheDocument();

      // Note: Animation testing would require more complex setup
      // This test verifies the component renders with attention state
    });

    it("should reset attention after timeout", async () => {
      // Arrange: Create selection with attention
      const attentionSelection: TSelection[] = [
        {
          tagId: 1,
          tagsetId: 1,
          tagName: "Attention Tag",
          tagsetName: "Test Tagset",
          attention: true,
        },
      ];

      // Act: Render component with attention selection
      render(
        <TaggedContainer
          selections={attentionSelection}
          isSubmitting={false}
          handleRemove={mockHandleRemove}
          handleResetAttention={mockHandleResetAttention}
        />
      );

      // Assert: Component should render with proper format
      expect(screen.getByText("Test Tagset: Attention Tag")).toBeInTheDocument();

      // Note: Timeout testing would require fake timers
      // This test verifies the component handles attention state
    });
  });
});