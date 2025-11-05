import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { TTagset } from "~/domain/Tagset";
import { TaggingStep } from "~/features/workflows/tagging/instance-tagging/steps/Tagging";

// Mock the useSteppingContext hook
vi.mock("~/hooks/useSteppingContext", () => ({
  default: () => ({
    index: 0,
    last: false,
  }),
}));

describe("TaggingStep Component (Instance Tagging)", () => {
  // Arrange: Set up mock functions and test data
  const user = userEvent.setup();
  const mockOnSelection = vi.fn();
  const mockOnPaginate = vi.fn();

  const mockTagsets: TTagset[] = [
    {
      tagset_id: 1,
      tagset_name: "Empty Tagset",
      tagset_desc: "Empty tagset description",
      cardinality: "single",
      tagset_type: 1,
      scope: "Engagement",
      dc_engagement_id: 1,
      tags: [],
    },
    {
      tagset_id: 2,
      tagset_name: "Non-Empty Tagset",
      tagset_desc: "Non-empty tagset description",
      cardinality: "single",
      tagset_type: 1,
      scope: "Engagement",
      dc_engagement_id: 1,
      tags: [
        {
          tag_id: 1,
          tag_name: "Tag 1",
          tag_desc: "Tag 1 description",
          tagset_id: 2,
        },
      ],
    },
    {
      tagset_id: 3,
      tagset_name: "Global Empty",
      tagset_desc: "Global empty tagset description",
      cardinality: "single",
      tagset_type: 1,
      scope: "Global",
      tags: [],
    },
    {
      tagset_id: 4,
      tagset_name: "Global Non-Empty",
      tagset_desc: "Global non-empty tagset description",
      cardinality: "single",
      tagset_type: 1,
      scope: "Global",
      tags: [
        {
          tag_id: 2,
          tag_name: "Tag 2",
          tag_desc: "Tag 2 description",
          tagset_id: 4,
        },
      ],
    },
  ];

  const mockProps = {
    tagsets: mockTagsets,
    selections: [],
    onSelection: vi.fn(),
    onTagRemove: vi.fn(),
    onPaginate: vi.fn(),
    loading: false,
  };

  describe("Empty Tagset Filtering", () => {
    it("should not render tagsets with empty tags array", () => {
      // Act: Render component with mixed empty and non-empty tagsets
      render(<TaggingStep {...mockProps} />);

      // Assert: Empty tagsets should not be visible to user
      expect(screen.queryByText("Empty Tagset")).not.toBeInTheDocument();
      expect(screen.queryByText("Global Empty")).not.toBeInTheDocument();

      // Assert: Non-empty tagsets should be visible to user
      expect(screen.getByText("Non-Empty Tagset")).toBeInTheDocument();
      expect(screen.getByText("Global Non-Empty")).toBeInTheDocument();
    });

    it("should filter out tagsets with empty tags array", () => {
      // Arrange: Create test data with one empty and one valid tagset
      const tagsetsWithEmptyArrays: TTagset[] = [
        {
          tagset_id: 1,
          tagset_name: "Empty Array Tagset",
          tagset_desc: "Empty array tagset description",
          cardinality: "single",
          tagset_type: 1,
          scope: "Engagement",
          dc_engagement_id: 1,
          tags: [],
        },
        {
          tagset_id: 2,
          tagset_name: "Valid Tagset",
          tagset_desc: "Valid tagset description",
          cardinality: "single",
          tagset_type: 1,
          scope: "Engagement",
          dc_engagement_id: 1,
          tags: [
            {
              tag_id: 1,
              tag_name: "Valid Tag",
              tag_desc: "Valid tag description",
              tagset_id: 2,
            },
          ],
        },
      ];

      // Act: Render component with the test data
      render(
        <TaggingStep
          tagsets={tagsetsWithEmptyArrays}
          selections={[]}
          onSelection={vi.fn()}
          onTagRemove={vi.fn()}
          onPaginate={mockOnPaginate}
          loading={false}
        />
      );

      // Assert: Empty tagset should not be visible, valid tagset should be visible
      expect(screen.queryByText("Empty Array Tagset")).not.toBeInTheDocument();
      expect(screen.getByText("Valid Tagset")).toBeInTheDocument();
    });
  });

  describe("Tag Toggle Functionality", () => {
    it("should toggle tag selection (deselect when already selected)", async () => {
      const mockOnTagRemove = vi.fn();
      const existingSelections = [
        {
          tagId: 1,
          tagsetId: 2, // Use tagset 2 which has "Tag 1"
          tagName: "Tag 1",
          tagsetName: "Non-Empty Tagset",
          attention: false,
        },
      ];

      render(
        <TaggingStep
          {...mockProps}
          selections={existingSelections}
          onTagRemove={mockOnTagRemove}
        />
      );

      // First expand the accordion to see the tag
      const accordion = screen.getByText("Non-Empty Tagset");
      await user.click(accordion);

      // Click on a tag that's already selected
      const tagChip = screen.getByText("Tag 1");
      await user.click(tagChip);

      // Should call onTagRemove with the existing selection
      expect(mockOnTagRemove).toHaveBeenCalledWith(existingSelections[0]);
    });
  });

  it("should handle empty tagsets array", () => {
    // Act: Render component with empty tagsets array
    render(
      <TaggingStep
        tagsets={[]}
        selections={[]}
        onSelection={vi.fn()}
        onTagRemove={vi.fn()}
        onPaginate={mockOnPaginate}
        loading={false}
      />
    );

    // Assert: No tagset names should be visible to user
    expect(screen.queryByText("Empty Tagset")).not.toBeInTheDocument();
    expect(screen.queryByText("Non-Empty Tagset")).not.toBeInTheDocument();
    expect(screen.queryByText("Global Empty")).not.toBeInTheDocument();
    expect(screen.queryByText("Global Non-Empty")).not.toBeInTheDocument();
  });

  it("should display loading state when data is being fetched", () => {
    // Act: Render component in loading state
    render(
      <TaggingStep
        tagsets={mockTagsets}
        selections={[]}
        onSelection={vi.fn()}
        onTagRemove={vi.fn()}
        onPaginate={mockOnPaginate}
        loading={true}
      />
    );

    // Assert: Loading skeletons should be visible to user (one for each section)
    const skeletons = screen
      .getAllByRole("generic")
      .filter((el) => el.className.includes("MuiSkeleton-root"));
    expect(skeletons).toHaveLength(2);
  });
});
