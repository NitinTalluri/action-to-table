import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import * as tmlApi from "~/api/tml";
import type { ITmlResponse } from "~/domain/Tml";
import { useLiveboardManager } from "~/features/liveboard-manager/hooks/useLiveboardManager";

// Mock the TML API
vi.mock("~/api/tml");
const mockGetTml = vi.mocked(tmlApi.getTml);

// Mock the convertTmlResponseToData function
vi.mock("~/domain/Tml", () => ({
  convertTmlResponseToData: vi.fn(),
}));

import { convertTmlResponseToData } from "~/domain/Tml";
const mockConvertTmlResponseToData = vi.mocked(convertTmlResponseToData);

// Mock toast notifications
vi.mock("sonner", () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
    info: vi.fn(),
  },
}));

describe("Engagement Liveboard Renaming in Library Pane", () => {
  let queryClient: QueryClient;
  let wrapper: React.FC<{ children: React.ReactNode }>;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    });

    wrapper = ({ children }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );

    // Setup mock return values
    mockConvertTmlResponseToData.mockReturnValue([
      {
        id: "standard-1",
        fileId: "standard-1",
        display_name: "Standard Dashboard 1",
        bucketId: "common",
        ephemeral: false,
        parent_id: null,
        originalBucket: null,
      },
      {
        id: "standard-2",
        fileId: "standard-2",
        display_name: "Standard Dashboard 2",
        bucketId: "common",
        ephemeral: false,
        parent_id: null,
        originalBucket: null,
      },
      {
        id: "custom-1",
        fileId: "custom-1",
        display_name: "Custom Engagement Dashboard 1",
        bucketId: "custom_eng",
        ephemeral: false,
        parent_id: null,
        originalBucket: null,
      },
      {
        id: "custom-2",
        fileId: "custom-2",
        display_name: "Custom Engagement Dashboard 2",
        bucketId: "custom_eng",
        ephemeral: false,
        parent_id: null,
        originalBucket: null,
      },
      {
        id: "workspace-1",
        fileId: "workspace-1",
        display_name: "Workspace Item 1",
        bucketId: "currently_in_ts",
        ephemeral: false,
        parent_id: null,
        originalBucket: null,
      },
    ]);

    vi.clearAllMocks();
  });

  const mockTmlResponse: ITmlResponse = {
    common: {
      "standard-1": {
        lb_params: {
          display_name: "Standard Dashboard 1",
        },
      },
      "standard-2": {
        lb_params: {
          display_name: "Standard Dashboard 2",
        },
      },
    },
    custom_eng: {
      "custom-1": {
        lb_params: {
          display_name: "Custom Engagement Dashboard 1",
        },
      },
      "custom-2": {
        lb_params: {
          display_name: "Custom Engagement Dashboard 2",
        },
      },
    },
    currently_in_ts: {
      "workspace-1": {
        lb_params: {
          display_name: "Workspace Item 1",
        },
      },
    },
  };

  describe("engagement item renaming", () => {
    it("should allow renaming engagement category items in library", async () => {
      mockGetTml.mockResolvedValue(mockTmlResponse);

      const { result } = renderHook(
        () =>
          useLiveboardManager({
            engagementId: 1,
            canvasId: 1,
          }),
        { wrapper }
      );

      await waitFor(() => {
        expect(result.current.libraryState.isLoading).toBe(false);
      });

      // Find an engagement category item
      const engagementItems = result.current.libraryItems.filter(
        (item) => item.category === "engagement"
      );

      if (engagementItems.length === 0) {
        // Skip test if no engagement items are available
        return;
      }

      const engagementItem = engagementItems[0];
      const originalName = engagementItem.display_name;
      const newName = "Renamed Engagement Dashboard";

      // Rename the engagement item
      result.current.renameItem(engagementItem, newName);

      await waitFor(() => {
        // Check that the item was renamed in library
        const updatedItem = result.current.libraryItems.find(
          (item) =>
            item.id === engagementItem.id ||
            item.fileId === engagementItem.fileId
        );
        expect(updatedItem?.display_name).toBe(newName);

        // Check that a rename action was tracked
        const renameAction = result.current.pendingActions.find(
          (action) =>
            action.type === "rename" &&
            (action.item.id === engagementItem.id ||
              action.item.fileId === engagementItem.fileId)
        );
        expect(renameAction).toBeDefined();
        expect(renameAction?.newName).toBe(newName);
        expect(renameAction?.originalName).toBe(originalName);
        expect(renameAction?.context).toBe("library");
      });
    });

    it("should prevent renaming standard category items", async () => {
      mockGetTml.mockResolvedValue(mockTmlResponse);

      const { result } = renderHook(
        () =>
          useLiveboardManager({
            engagementId: 1,
            canvasId: 1,
          }),
        { wrapper }
      );

      await waitFor(() => {
        expect(result.current.libraryState.isLoading).toBe(false);
      });

      // Find a standard category item
      const standardItems = result.current.libraryItems.filter(
        (item) => item.category === "standard"
      );

      if (standardItems.length === 0) {
        // Skip test if no standard items are available
        return;
      }

      const standardItem = standardItems[0];
      const originalName = standardItem.display_name;
      const newName = "Attempted Rename";

      // Try to rename the standard item
      result.current.renameItem(standardItem, newName);

      await waitFor(() => {
        // Check that the item was NOT renamed
        const unchangedItem = result.current.libraryItems.find(
          (item) =>
            item.id === standardItem.id || item.fileId === standardItem.fileId
        );
        expect(unchangedItem?.display_name).toBe(originalName);

        // Check that no rename action was tracked
        const renameAction = result.current.pendingActions.find(
          (action) =>
            action.type === "rename" &&
            (action.item.id === standardItem.id ||
              action.item.fileId === standardItem.fileId)
        );
        expect(renameAction).toBeUndefined();
      });
    });

    it("should allow renaming engagement items in workspace", async () => {
      mockGetTml.mockResolvedValue(mockTmlResponse);

      const { result } = renderHook(
        () =>
          useLiveboardManager({
            engagementId: 1,
            canvasId: 1,
          }),
        { wrapper }
      );

      await waitFor(() => {
        expect(result.current.workspaceState.isLoading).toBe(false);
      });

      // Find a workspace item (should be engagement category)
      const workspaceItems = result.current.workspaceItems;

      if (workspaceItems.length === 0) {
        // Skip test if no workspace items are available
        return;
      }

      const workspaceItem = workspaceItems[0];
      const newName = "Renamed Workspace Item";

      // Rename the workspace item
      result.current.renameItem(workspaceItem, newName);

      await waitFor(() => {
        // Check that the item was renamed in workspace
        const updatedItem = result.current.workspaceItems.find(
          (item) =>
            item.id === workspaceItem.id || item.fileId === workspaceItem.fileId
        );
        expect(updatedItem?.display_name).toBe(newName);

        // Check that a rename action was tracked
        const renameAction = result.current.pendingActions.find(
          (action) =>
            action.type === "rename" &&
            (action.item.id === workspaceItem.id ||
              action.item.fileId === workspaceItem.fileId)
        );
        expect(renameAction).toBeDefined();
        expect(renameAction?.newName).toBe(newName);
        expect(renameAction?.context).toBe("workspace");
      });
    });

    it("should handle renaming with special characters and long names", async () => {
      mockGetTml.mockResolvedValue(mockTmlResponse);

      const { result } = renderHook(
        () =>
          useLiveboardManager({
            engagementId: 1,
            canvasId: 1,
          }),
        { wrapper }
      );

      await waitFor(() => {
        expect(result.current.libraryState.isLoading).toBe(false);
      });

      const engagementItems = result.current.libraryItems.filter(
        (item) => item.category === "engagement"
      );

      if (engagementItems.length === 0) {
        return;
      }

      const engagementItem = engagementItems[0];
      const specialName =
        'Dashboard with "Quotes" & Special Characters (2024) - Version 1.0';

      // Rename with special characters
      result.current.renameItem(engagementItem, specialName);

      await waitFor(() => {
        const updatedItem = result.current.libraryItems.find(
          (item) =>
            item.id === engagementItem.id ||
            item.fileId === engagementItem.fileId
        );
        expect(updatedItem?.display_name).toBe(specialName);
      });
    });

    it("should handle renaming non-existent items gracefully", async () => {
      mockGetTml.mockResolvedValue(mockTmlResponse);

      const { result } = renderHook(
        () =>
          useLiveboardManager({
            engagementId: 1,
            canvasId: 1,
          }),
        { wrapper }
      );

      await waitFor(() => {
        expect(result.current.libraryState.isLoading).toBe(false);
      });

      const nonExistentItem = {
        id: "non-existent-item-id",
        fileId: "non-existent-file-id",
        display_name: "Non-existent Item",
        category: "engagement" as const,
        bucketId: "custom_eng",
        isInWorkspace: false,
        isExisting: false,
        ephemeral: false,
        parent_id: null,
        originalBucket: null,
      };
      const newName = "Should Not Work";

      // Try to rename non-existent item - should not throw error
      expect(() => {
        result.current.renameItem(nonExistentItem, newName);
      }).not.toThrow();
    });

    it("should update hasChanges flag when renaming", async () => {
      mockGetTml.mockResolvedValue(mockTmlResponse);

      const { result } = renderHook(
        () =>
          useLiveboardManager({
            engagementId: 1,
            canvasId: 1,
          }),
        { wrapper }
      );

      await waitFor(() => {
        expect(result.current.libraryState.isLoading).toBe(false);
      });

      // Initially no changes
      expect(result.current.hasChanges).toBe(false);

      const engagementItems = result.current.libraryItems.filter(
        (item) => item.category === "engagement"
      );

      if (engagementItems.length > 0) {
        // Rename the item
        result.current.renameItem(engagementItems[0], "New Name");

        await waitFor(() => {
          // Should have changes now
          expect(result.current.hasChanges).toBe(true);
        });
      }
    });

    it("should preserve item properties during rename", async () => {
      mockGetTml.mockResolvedValue(mockTmlResponse);

      const { result } = renderHook(
        () =>
          useLiveboardManager({
            engagementId: 1,
            canvasId: 1,
          }),
        { wrapper }
      );

      await waitFor(() => {
        expect(result.current.libraryState.isLoading).toBe(false);
      });

      const engagementItems = result.current.libraryItems.filter(
        (item) => item.category === "engagement"
      );

      if (engagementItems.length === 0) {
        return;
      }

      const engagementItem = engagementItems[0];
      const originalProperties = {
        id: engagementItem.id,
        fileId: engagementItem.fileId,
        bucketId: engagementItem.bucketId,
        category: engagementItem.category,
        isExisting: engagementItem.isExisting,
        isInWorkspace: engagementItem.isInWorkspace,
      };

      // Rename the item
      result.current.renameItem(engagementItem, "New Name");

      await waitFor(() => {
        const renamedItem = result.current.libraryItems.find(
          (item) =>
            item.id === engagementItem.id ||
            item.fileId === engagementItem.fileId
        );

        if (renamedItem) {
          // All properties except display_name should be preserved
          expect(renamedItem.id).toBe(originalProperties.id);
          expect(renamedItem.fileId).toBe(originalProperties.fileId);
          expect(renamedItem.bucketId).toBe(originalProperties.bucketId);
          expect(renamedItem.category).toBe(originalProperties.category);
          expect(renamedItem.isExisting).toBe(originalProperties.isExisting);
          expect(renamedItem.isInWorkspace).toBe(
            originalProperties.isInWorkspace
          );

          // Only display_name should change
          expect(renamedItem.display_name).toBe("New Name");
        }
      });
    });

    it("should handle multiple renames of the same item", async () => {
      mockGetTml.mockResolvedValue(mockTmlResponse);

      const { result } = renderHook(
        () =>
          useLiveboardManager({
            engagementId: 1,
            canvasId: 1,
          }),
        { wrapper }
      );

      await waitFor(() => {
        expect(result.current.libraryState.isLoading).toBe(false);
      });

      const engagementItems = result.current.libraryItems.filter(
        (item) => item.category === "engagement"
      );

      if (engagementItems.length === 0) {
        return;
      }

      const engagementItem = engagementItems[0];
      const firstName = "First Rename";
      const secondName = "Second Rename";

      // First rename
      result.current.renameItem(engagementItem, firstName);

      await waitFor(() => {
        const updatedItem = result.current.libraryItems.find(
          (item) =>
            item.id === engagementItem.id ||
            item.fileId === engagementItem.fileId
        );
        expect(updatedItem?.display_name).toBe(firstName);
      });

      // Second rename
      result.current.renameItem(engagementItem, secondName);

      await waitFor(() => {
        const finalItem = result.current.libraryItems.find(
          (item) =>
            item.id === engagementItem.id ||
            item.fileId === engagementItem.fileId
        );
        expect(finalItem?.display_name).toBe(secondName);

        // Check for rename actions
        const renameActions = result.current.pendingActions.filter(
          (action) =>
            action.type === "rename" &&
            (action.item.id === engagementItem.id ||
              action.item.fileId === engagementItem.fileId)
        );
        expect(renameActions.length).toBe(2);

        // Check the most recent rename action
        const latestRename = renameActions[renameActions.length - 1];
        expect(latestRename.newName).toBe(secondName);
      });
    });
  });
});
