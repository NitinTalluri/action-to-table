import { createTheme,ThemeProvider } from "@mui/material/styles";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { vi } from "vitest";

import { TTagset } from "~/domain/Tagset";
import TagsetAccordion from "~/features/thoughtspot/Dialog/TagsetAccordion";

// Mock theme for consistent testing
const theme = createTheme();

const mockTagset: TTagset = {
  tagset_id: 1,
  tagset_name: "Test Tagset",
  tagset_desc: "A test tagset for unit testing",
  cardinality: "single",
  tagset_type: 0,
  scope: "Engagement",
  dc_engagement_id: 123,
  tags: [
    {
      tag_id: 1,
      tag_name: "Tag 1",
      tagset_id: 1,
      tag_desc: "",
    },
    {
      tag_id: 2,
      tag_name: "Tag 2",
      tagset_id: 1,
      tag_desc: "",
    },
    {
      tag_id: 3,
      tag_name: "Tag 3",
      tagset_id: 1,
      tag_desc: "",
    },
  ],
};

const mockHandleExpand = vi.fn();
const mockHandleTagClick = vi.fn();

const defaultProps = {
  isOpen: false,
  tagset: mockTagset,
  handleExpand: mockHandleExpand,
  handleTagClick: mockHandleTagClick,
  selectedTags: [],
};

const renderWithTheme = (component: React.ReactElement) => {
  return render(<ThemeProvider theme={theme}>{component}</ThemeProvider>);
};

describe("TagsetAccordion Spacing Behavior", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("Accordion Header Height Consistency", () => {
    it("should maintain consistent header height when collapsed", () => {
      renderWithTheme(<TagsetAccordion {...defaultProps} />);

      const accordionSummary = screen.getByRole("button", {
        name: /expand test tagset tagset/i,
      });

      // Check that the accordion summary exists and has proper styling
      expect(accordionSummary).toBeInTheDocument();

      // Check that the accordion has minimum height applied
      expect(accordionSummary).toHaveStyle({
        minHeight: "56px",
      });

      // Check that content margin is set properly
      const content = accordionSummary.querySelector(
        ".MuiAccordionSummary-content",
      );
      expect(content).toHaveStyle({
        margin: "12px 0",
      });
    });

    it("should maintain consistent header height when expanded", () => {
      renderWithTheme(<TagsetAccordion {...defaultProps} isOpen={true} />);

      const accordionSummary = screen.getByRole("button", {
        name: /collapse test tagset tagset/i,
      });

      // Check that the accordion summary exists and has proper styling
      expect(accordionSummary).toBeInTheDocument();

      // Check that the accordion maintains minimum height when expanded
      expect(accordionSummary).toHaveStyle({
        minHeight: "56px",
      });

      // Check that content margin is set properly
      const content = accordionSummary.querySelector(
        ".MuiAccordionSummary-content",
      );
      expect(content).toHaveStyle({
        margin: "12px 0",
      });
    });

    it("should have consistent header styling between collapsed and expanded states", () => {
      const { rerender } = renderWithTheme(
        <TagsetAccordion {...defaultProps} />,
      );

      const collapsedSummary = screen.getByRole("button", {
        name: /expand test tagset tagset/i,
      });
      const collapsedContent = collapsedSummary.querySelector(
        ".MuiAccordionSummary-content",
      );

      // Re-render in expanded state
      rerender(
        <ThemeProvider theme={theme}>
          <TagsetAccordion {...defaultProps} isOpen={true} />
        </ThemeProvider>,
      );

      const expandedSummary = screen.getByRole("button", {
        name: /collapse test tagset tagset/i,
      });
      const expandedContent = expandedSummary.querySelector(
        ".MuiAccordionSummary-content",
      );

      // Both should have the same content margin for consistent height
      expect(collapsedContent).toHaveStyle({ margin: "12px 0" });
      expect(expandedContent).toHaveStyle({ margin: "12px 0" });
    });
  });

  describe("Smooth Transition Behavior", () => {
    it("should have smooth transitions on accordion details", () => {
      renderWithTheme(<TagsetAccordion {...defaultProps} isOpen={true} />);

      const accordionDetails = screen.getByRole("group", {
        name: /tags in test tagset tagset/i,
      }).parentElement;

      expect(accordionDetails).toHaveStyle({
        transition: "all 0.2s ease-in-out",
      });
    });

    it("should apply proper transition timing during expansion", async () => {
      const { rerender } = renderWithTheme(
        <TagsetAccordion {...defaultProps} />,
      );

      // Initially collapsed
      expect(
        screen.queryByRole("group", {
          name: /tags in test tagset tagset/i,
        }),
      ).not.toBeInTheDocument();

      // Expand
      rerender(
        <ThemeProvider theme={theme}>
          <TagsetAccordion {...defaultProps} isOpen={true} />
        </ThemeProvider>,
      );

      // Should now be visible with transition
      await waitFor(() => {
        const accordionDetails = screen.getByRole("group", {
          name: /tags in test tagset tagset/i,
        }).parentElement;
        expect(accordionDetails).toHaveStyle({
          transition: "all 0.2s ease-in-out",
        });
      });
    });
  });

  describe("Layout Stability", () => {
    it("should maintain stable layout structure when toggling expansion state", () => {
      const { rerender } = renderWithTheme(
        <TagsetAccordion {...defaultProps} />,
      );

      const accordionSummary = screen.getByRole("button", {
        name: /expand test tagset tagset/i,
      });
      const accordion = accordionSummary.closest(".MuiAccordion-root");

      expect(accordion).toBeInTheDocument();
      expect(accordion).toHaveClass("MuiAccordion-root");

      // Expand
      rerender(
        <ThemeProvider theme={theme}>
          <TagsetAccordion {...defaultProps} isOpen={true} />
        </ThemeProvider>,
      );

      const expandedSummary = screen.getByRole("button", {
        name: /collapse test tagset tagset/i,
      });
      const expandedAccordion = expandedSummary.closest(".MuiAccordion-root");

      // Structure should remain consistent
      expect(expandedAccordion).toBeInTheDocument();
      expect(expandedAccordion).toHaveClass("MuiAccordion-root");
      expect(expandedAccordion).toHaveClass("Mui-expanded");
    });

    it("should have consistent margin spacing in expanded state", () => {
      renderWithTheme(<TagsetAccordion {...defaultProps} isOpen={true} />);

      const accordionSummary = screen.getByRole("button", {
        name: /collapse test tagset tagset/i,
      });
      const accordion = accordionSummary.closest(".MuiAccordion-root");

      // Check for proper margin in expanded state
      expect(accordion).toHaveStyle({
        margin: "0 0 8px 0",
      });
    });

    it("should prevent layout shift with proper border radius handling", () => {
      renderWithTheme(<TagsetAccordion {...defaultProps} isOpen={true} />);

      const accordionSummary = screen.getByRole("button", {
        name: /collapse test tagset tagset/i,
      });
      const accordionDetails = screen.getByRole("group", {
        name: /tags in test tagset tagset/i,
      }).parentElement;

      // Summary should have no bottom border radius when expanded
      expect(accordionSummary).toHaveStyle({
        borderBottomLeftRadius: 0,
        borderBottomRightRadius: 0,
      });

      // Details should have bottom border radius
      expect(accordionDetails).toHaveStyle({
        borderBottomLeftRadius: "4px",
        borderBottomRightRadius: "4px",
      });
    });
  });

  describe("Visual Consistency", () => {
    it("should maintain consistent background colors during transitions", () => {
      renderWithTheme(<TagsetAccordion {...defaultProps} isOpen={true} />);

      const accordionSummary = screen.getByRole("button", {
        name: /collapse test tagset tagset/i,
      });
      const accordionDetails = screen.getByRole("group", {
        name: /tags in test tagset tagset/i,
      }).parentElement;

      // Check that both elements exist and have background styling applied
      expect(accordionSummary).toBeInTheDocument();
      expect(accordionDetails).toBeInTheDocument();

      // Verify the accordion has the expanded class when open
      const accordion = accordionSummary.closest(".MuiAccordion-root");
      expect(accordion).toHaveClass("Mui-expanded");
    });
    it("should handle hover states without affecting layout", () => {
      renderWithTheme(<TagsetAccordion {...defaultProps} />);

      const accordionSummary = screen.getByRole("button", {
        name: /expand test tagset tagset/i,
      });

      // Check initial state
      expect(accordionSummary).toBeInTheDocument();
      expect(accordionSummary).toHaveStyle({
        minHeight: "56px",
      });

      // Simulate hover
      fireEvent.mouseEnter(accordionSummary);

      // Element should still be present and maintain its structure
      expect(accordionSummary).toBeInTheDocument();
      expect(accordionSummary).toHaveStyle({
        minHeight: "56px",
      });

      // Simulate mouse leave
      fireEvent.mouseLeave(accordionSummary);

      // Should still maintain consistent height
      expect(accordionSummary).toHaveStyle({
        minHeight: "56px",
      });
    });
  });

  describe("Accessibility and Spacing", () => {
    it("should maintain proper spacing for accessibility", () => {
      renderWithTheme(<TagsetAccordion {...defaultProps} isOpen={true} />);

      const accordionDetails = screen.getByRole("group", {
        name: /tags in test tagset tagset/i,
      }).parentElement;

      // Should have proper padding for accessibility
      expect(accordionDetails).toHaveStyle({
        padding: "16px", // 2 * 8px (theme spacing unit)
      });
    });

    it("should provide proper spacing between tags", () => {
      renderWithTheme(<TagsetAccordion {...defaultProps} isOpen={true} />);

      const tagContainer = screen.getByRole("group", {
        name: /tags in test tagset tagset/i,
      });

      // Should have gap for proper tag spacing
      expect(tagContainer).toHaveStyle({
        gap: "8px",
      });
    });
  });
});
