import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import {
  IWorkspacePaneProps,
  WorkspacePane,
} from "~/features/liveboard-manager/components/WorkspacePane";
import type { ILiveboardItem } from "~/features/liveboard-manager/types";

const mockWorkspaceItems: ILiveboardItem[] = [
  {
    id: "1",
    fileId: "asset-overview",
    display_name: "Asset Overview",
    bucketId: "currently_in_ts",
    ephemeral: false,
    category: "standard",
    isInWorkspace: true,
    parent_id: null,
    originalBucket: null,
  },
  {
    id: "2",
    fileId: "custom-report",
    display_name: "Custom Report",
    bucketId: "currently_in_ts",
    ephemeral: true,
    category: "engagement",
    isInWorkspace: true,
    parent_id: null,
    originalBucket: null,
  },
];

const mockProps: IWorkspacePaneProps = {
  state: {
    items: mockWorkspaceItems,
    hasChanges: false,
    isLoading: false,
    actions: [],
  },
  canvasName: "Test Canvas",
  canvasId: 123,
  onRemoveFromWorkspace: vi.fn(),
  onRename: vi.fn(),
  onCopy: vi.fn(),
  onSaveAsTemplate: vi.fn(),
  onDelete: vi.fn(),
};

describe("WorkspacePane", () => {
  it("renders the workspace header with canvas info", () => {
    render(<WorkspacePane {...mockProps} />);

    expect(screen.getByText("Active Workspace")).toBeInTheDocument();
    expect(screen.getByText(/Test Canvas \(123\)/)).toBeInTheDocument();
  });

  it("displays workspace items", () => {
    render(<WorkspacePane {...mockProps} />);

    expect(screen.getByText("Asset Overview")).toBeInTheDocument();
    expect(screen.getByText("Custom Report")).toBeInTheDocument();
  });

  it("shows empty state when no items", () => {
    const emptyProps = {
      ...mockProps,
      state: { ...mockProps.state, items: [] },
    };

    render(<WorkspacePane {...emptyProps} />);

    expect(screen.getByText(/No liveboards in workspace/)).toBeInTheDocument();
    expect(
      screen.getByText(/Add liveboards from the library/)
    ).toBeInTheDocument();
  });

  it("shows changes indicator when hasChanges is true", () => {
    const changedProps = {
      ...mockProps,
      state: { ...mockProps.state, hasChanges: true },
    };

    render(<WorkspacePane {...changedProps} />);

    expect(screen.getByText(/Unsaved changes/)).toBeInTheDocument();
  });

  it("shows loading state", () => {
    const loadingProps = {
      ...mockProps,
      state: { ...mockProps.state, isLoading: true },
    };

    render(<WorkspacePane {...loadingProps} />);

    expect(screen.getByRole("progressbar")).toBeInTheDocument();
  });

  it("calls onRemoveFromWorkspace when remove button is clicked", async () => {
    const user = userEvent.setup();
    render(<WorkspacePane {...mockProps} />);

    // Find and click the first remove button by title attribute
    const removeButtons = screen.getAllByTitle("Remove from workspace");
    await user.click(removeButtons[0]);

    expect(mockProps.onRemoveFromWorkspace).toHaveBeenCalledWith(
      mockWorkspaceItems[0]
    );
  });
});
