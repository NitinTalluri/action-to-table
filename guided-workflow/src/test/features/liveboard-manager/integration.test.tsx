import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { LiveboardManager } from "~/features/liveboard-manager/components/LiveboardManager";
import type { ILiveboardManagerProps } from "~/features/liveboard-manager/types";

// Mock the TML query
vi.mock("~/queries/tml", () => ({
  tmlQuery: () => ({
    queryKey: ["tml", { dc_engagement_id: 1, canvas_id: 1 }],
    queryFn: () =>
      Promise.resolve({
        common: [
          {
            id: "common-1",
            fileId: "asset-overview",
            display_name: "Asset Overview",
            bucketId: "common",
            ephemeral: false,
          },
        ],
        custom_eng: [],
        custom_user: [],
        currently_in_ts: [],
        delete: [],
      }),
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

describe("LiveboardManager Integration", () => {
  it("renders and loads TML data", async () => {
    renderWithQueryClient(<LiveboardManager {...mockProps} />);

    expect(screen.getByRole("dialog")).toBeInTheDocument();
    expect(screen.getByText("Liveboard Manager")).toBeInTheDocument();

    // Wait for data to load
    await waitFor(
      () => {
        expect(screen.getByText("Asset Overview")).toBeInTheDocument();
      },
      { timeout: 3000 },
    );
  });
});
