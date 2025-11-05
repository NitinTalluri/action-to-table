import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import {
  ILibraryPaneProps,
  LibraryPane,
} from "~/features/liveboard-manager/components/LibraryPane";
import type { ILiveboardItem } from "~/features/liveboard-manager/types";

const mockItems: ILiveboardItem[] = [
  {
    id: "1",
    fileId: "asset-overview",
    display_name: "Asset Overview",
    bucketId: "common",
    ephemeral: false,
    category: "standard",
    isInWorkspace: false,
    parent_id: null,
    originalBucket: null,
  },
  {
    id: "2",
    fileId: "custom-report",
    display_name: "Custom Report",
    bucketId: "custom_user",
    ephemeral: true,
    category: "engagement",
    isInWorkspace: false,
    parent_id: null,
    originalBucket: null,
  },
];

const mockProps: ILibraryPaneProps = {
  state: {
    searchQuery: "",
    activeFilter: "all",
    items: mockItems,
    filteredItems: mockItems,
    isLoading: false,
  },
  onSearchChange: vi.fn(),
  onFilterChange: vi.fn(),
  onAddToWorkspace: vi.fn(),
  onCopy: vi.fn(),
  onDelete: vi.fn(),
  onRename: vi.fn(),
};

describe("LibraryPane", () => {
  it("renders the library header", () => {
    render(<LibraryPane {...mockProps} />);

    expect(screen.getByText("Liveboard Library")).toBeInTheDocument();
  });

  it("renders the search bar", () => {
    render(<LibraryPane {...mockProps} />);

    expect(
      screen.getByPlaceholderText("Search liveboards...")
    ).toBeInTheDocument();
  });

  it("renders filter tabs", () => {
    render(<LibraryPane {...mockProps} />);

    expect(screen.getByText("All (2)")).toBeInTheDocument();
    expect(screen.getByText("Standard Templates (1)")).toBeInTheDocument();
    expect(screen.getByText("Engagement Templates (0)")).toBeInTheDocument();
  });

  it("displays liveboard items", () => {
    render(<LibraryPane {...mockProps} />);

    expect(screen.getByText("Asset Overview")).toBeInTheDocument();
    expect(screen.getByText("Custom Report")).toBeInTheDocument();
  });

  it("calls onSearchChange when typing in search", async () => {
    const user = userEvent.setup();
    const onSearchChange = vi.fn();

    render(<LibraryPane {...mockProps} onSearchChange={onSearchChange} />);

    const searchInput = screen.getByPlaceholderText("Search liveboards...");
    await user.type(searchInput, "asset");

    await waitFor(() => {
      expect(onSearchChange).toHaveBeenCalledWith("asset");
    });
  });

  it("calls onFilterChange when clicking filter tabs", async () => {
    const user = userEvent.setup();
    const onFilterChange = vi.fn();

    render(<LibraryPane {...mockProps} onFilterChange={onFilterChange} />);

    await user.click(screen.getByText("Standard Templates (1)"));

    expect(onFilterChange).toHaveBeenCalledWith("standard");
  });

  it("shows loading state", () => {
    const loadingProps = {
      ...mockProps,
      state: { ...mockProps.state, isLoading: true },
    };

    render(<LibraryPane {...loadingProps} />);

    expect(screen.getByRole("progressbar")).toBeInTheDocument();
  });

  it("shows empty state when no items", () => {
    const emptyProps = {
      ...mockProps,
      state: {
        ...mockProps.state,
        items: [],
        filteredItems: [],
      },
    };

    render(<LibraryPane {...emptyProps} />);

    expect(screen.getByText("No liveboards available")).toBeInTheDocument();
  });
});
