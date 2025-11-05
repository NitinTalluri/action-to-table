import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { LiveboardManager } from "~/features/liveboard-manager/components/LiveboardManager";
import type { ILiveboardManagerProps } from "~/features/liveboard-manager/types";

// Mock the hooks and components that will be created
vi.mock("~/features/liveboard-manager/hooks/useLiveboardManager", () => ({
  useLiveboardManager: () => ({
    libraryItems: [],
    workspaceItems: [],
    searchTerm: "",
    setSearchTerm: vi.fn(),
    activeFilter: "all" as const,
    setActiveFilter: vi.fn(),
    addToWorkspace: vi.fn(),
    removeFromWorkspace: vi.fn(),
    clearWorkspace: vi.fn(),
    isLoading: false,
    error: null,
  }),
}));

const mockProps: ILiveboardManagerProps = {
  engagement: {
    dc_engagement_id: 1,
    engagement_name: "Test Engagement",
    created_by: "",
    create_dtm: "",
    update_dtm: null,
    updated_by: null,
    is_deleted: false,
    is_sfc: false,
    is_cxea: false,
    is_software: false,
    sfc_agreement_type: 0,
    notes: "",
  },
  canvas: {
    canvas_id: 1,
    canvas_name: "Test Canvas",
    create_dtm: "",
    dc_engagement_id: 0,
    canvas_desc: "",
    canvas_status: "running",
    canvas_type: "current view canvas",
    pinboards: [],
    extract_actions: 0,
    tag_actions: 0,
    notification_id: null,
  },
  onClose: vi.fn(),
  onDiscover: vi.fn(),
  isOpen: true,
};

const renderWithQueryClient = (component: React.ReactElement) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return render(
    <QueryClientProvider client={queryClient}>{component}</QueryClientProvider>,
  );
};

describe("LiveboardManager", () => {
  it("renders the main dialog when open", () => {
    renderWithQueryClient(<LiveboardManager {...mockProps} />);

    expect(screen.getByRole("dialog")).toBeInTheDocument();
  });

  it("displays the canvas and engagement information in title", () => {
    renderWithQueryClient(<LiveboardManager {...mockProps} />);

    // Use getAllByText since the canvas name appears in both title and workspace pane
    const canvasElements = screen.getAllByText(/Test Canvas/);
    expect(canvasElements.length).toBeGreaterThan(0);
    expect(screen.getByText(/Test Engagement/)).toBeInTheDocument();
  });

  it("renders library and workspace panes", () => {
    renderWithQueryClient(<LiveboardManager {...mockProps} />);

    // Look for the text with emojis
    expect(screen.getByText("📚 Liveboard Library")).toBeInTheDocument();
    expect(screen.getByText("🎯 Active Workspace")).toBeInTheDocument();
  });

  it("does not render when closed", () => {
    renderWithQueryClient(<LiveboardManager {...mockProps} isOpen={false} />);

    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  it("calls onClose when cancel button is clicked", () => {
    const onClose = vi.fn();
    renderWithQueryClient(
      <LiveboardManager {...mockProps} onClose={onClose} />,
    );

    const cancelButton = screen.getByText("Cancel");
    cancelButton.click();

    expect(onClose).toHaveBeenCalled();
  });
});
