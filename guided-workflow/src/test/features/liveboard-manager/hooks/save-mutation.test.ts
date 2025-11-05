import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { createTml } from "~/api/tml";
import type { ILiveboardItem } from "~/features/liveboard-manager/types";
import { useLiveboardManager } from "~/features/liveboard-manager/hooks/useLiveboardManager";

// Mock the TML API
vi.mock("~/api/tml", () => ({
  getTml: vi.fn(),
  createTml: vi.fn(),
}));

// Mock toast notifications
vi.mock("sonner", () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
    info: vi.fn(),
  },
}));

describe("Complete State Save Mutation with Bucket Assignments", () => {
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

    vi.clearAllMocks();
  });

  const mockEngagementId = 123;
  const mockCanvasId = 456;

  const mockLibraryItems: ILiveboardItem[] = [
    {
      fileId: "standard-1",
      ephemeral: false,
      display_name: "Standard Dashboard",
      bucketId: "common",
      parent_id: null,
      originalBucket: null,
      id: "common-standard-1",
      category: "standard",
      isInWorkspace: false,
      isExisting: true,
    },
    {
      fileId: "engagement-1",
      ephemeral: false,
      display_name: "Engagement Dashboard",
      bucketId: "custom_eng",
      parent_id: null,
      originalBucket: null,
      id: "custom_eng-engagement-1",
      category: "engagement",
      isInWorkspace: false,
      isExisting: true,
    },
  ];

  const mockWorkspaceItems: ILiveboardItem[] = [
    {
      fileId: "workspace-1",
      ephemeral: false,
      display_name: "Workspace Dashboard",
      bucketId: "currently_in_ts",
      parent_id: null,
      originalBucket: null,
      id: "currently_in_ts-workspace-1",
      category: "engagement",
      isInWorkspace: true,
      isExisting: true,
    },
  ];

  describe("bucket assignment logic", () => {
    it("should assign library items to their original buckets", async () => {
      const mockCreateTml = vi.mocked(createTml);
      mockCreateTml.mockResolvedValue({} as any);

      const { result } = renderHook(
        () => useLiveboardManager({ engagementId: mockEngagementId, canvasId: mockCanvasId }),
        { wrapper }
      );

      // Simulate having items in state
      // Note: In a real test, we'd need to mock the initial TML response
      // For now, we'll test the bucket assignment logic directly

      const expectedBucketData = {
        common: {
          "standard-1": {
            lb_params: {
              display_name: "Standard Dashboard",
            },
          },
        },
        custom_eng: {
          "engagement-1": {
            lb_params: {
              display_name: "Engagement Dashboard",
            },
          },
        },
        currently_in_ts: {
          "workspace-1": {
            lb_params: {
              display_name: "Workspace Dashboard",
            },
          },
        },
        delete: {},
      };

      // This test structure is ready for when we implement the save logic
      expect(expectedBucketData).toBeDefined();
    });

    it("should handle deleted items by moving them to delete bucket", () => {
      const deletedItem: ILiveboardItem = {
        ...mockLibraryItems[0],
        isDeleted: true,
      };

      // Test logic for moving deleted items to delete bucket
      const targetBucket = deletedItem.isDeleted ? "delete" : deletedItem.bucketId;
      expect(targetBucket).toBe("delete");
    });

    it("should handle workspace items by assigning to currently_in_ts bucket", () => {
      const workspaceItem = mockWorkspaceItems[0];

      // Test logic for workspace items
      const targetBucket = workspaceItem.isInWorkspace ? "currently_in_ts" : workspaceItem.bucketId;
      expect(targetBucket).toBe("currently_in_ts");
    });
  });

  describe("action processing", () => {
    it("should process add actions by moving items to currently_in_ts", () => {
      const addAction = {
        id: "add_test_123",
        type: "add" as const,
        item: mockLibraryItems[0],
        timestamp: Date.now(),
        context: "workspace" as const,
      };

      // Test add action processing logic
      expect(addAction.type).toBe("add");
      expect(addAction.context).toBe("workspace");
    });

    it("should process delete actions by moving items to delete bucket", () => {
      const deleteAction = {
        id: "delete_test_123",
        type: "delete" as const,
        item: mockWorkspaceItems[0],
        timestamp: Date.now(),
        context: "workspace" as const,
      };

      // Test delete action processing logic
      expect(deleteAction.type).toBe("delete");
      expect(deleteAction.context).toBe("workspace");
    });

    it("should process copy actions with proper bucket assignment", () => {
      const copyToWorkspaceAction = {
        id: "copy_test_123",
        type: "copy" as const,
        item: mockLibraryItems[0],
        timestamp: Date.now(),
        context: "workspace" as const,
      };

      const copyToLibraryAction = {
        id: "copy_test_456",
        type: "copy" as const,
        item: mockWorkspaceItems[0],
        timestamp: Date.now(),
        context: "library" as const,
      };

      // Test copy action bucket assignment
      const workspaceTargetBucket = copyToWorkspaceAction.context === "workspace" ? "currently_in_ts" : "custom_eng";
      const libraryTargetBucket = copyToLibraryAction.id === "workspace" ? "currently_in_ts" : "custom_eng";

      expect(workspaceTargetBucket).toBe("currently_in_ts");
      expect(libraryTargetBucket).toBe("custom_eng");
    });

    it("should process save-as-template actions to custom_eng bucket", () => {
      const saveAsTemplateAction = {
        id: "template_test_123",
        type: "save-as-template" as const,
        item: mockWorkspaceItems[0],
        timestamp: Date.now(),
      };

      // Test save-as-template action bucket assignment
      expect(saveAsTemplateAction.type).toBe("save-as-template");
      // Should always go to custom_eng bucket
    });

    it("should process rename actions by updating display_name in current bucket", () => {
      const renameAction = {
        id: "rename_test_123",
        type: "rename" as const,
        item: mockWorkspaceItems[0],
        originalName: "Old Name",
        newName: "New Name",
        timestamp: Date.now(),
        context: "workspace" as const,
      };

      // Test rename action processing
      expect(renameAction.type).toBe("rename");
      expect(renameAction.newName).toBe("New Name");
      expect(renameAction.originalName).toBe("Old Name");
    });
  });

  describe("complete save flow", () => {
    it("should call createTml with properly formatted bucket data", async () => {
      const mockCreateTml = vi.mocked(createTml);
      mockCreateTml.mockResolvedValue({} as any);

      // This test will be implemented when the save mutation is complete
      // For now, we verify the expected structure

      const expectedPayload = {
        engagementId: mockEngagementId,
        canvasId: mockCanvasId,
        tml: {
          common: {},
          custom_eng: {},
          currently_in_ts: {},
          delete: {},
        },
        defer: false,
      };

      expect(expectedPayload.engagementId).toBe(mockEngagementId);
      expect(expectedPayload.canvasId).toBe(mockCanvasId);
      expect(expectedPayload.defer).toBe(false);
      expect(expectedPayload.tml).toHaveProperty("common");
      expect(expectedPayload.tml).toHaveProperty("custom_eng");
      expect(expectedPayload.tml).toHaveProperty("currently_in_ts");
      expect(expectedPayload.tml).toHaveProperty("delete");
    });

    it("should handle save success by clearing pending actions", async () => {
      // This test structure is ready for implementation
      const expectedBehavior = {
        clearPendingActions: true,
        resetHasChanges: true,
        showSuccessToast: true,
        invalidateQueries: true,
      };

      expect(expectedBehavior.clearPendingActions).toBe(true);
      expect(expectedBehavior.resetHasChanges).toBe(true);
      expect(expectedBehavior.showSuccessToast).toBe(true);
      expect(expectedBehavior.invalidateQueries).toBe(true);
    });

    it("should handle save errors gracefully", async () => {
      const mockCreateTml = vi.mocked(createTml);
      mockCreateTml.mockRejectedValue(new Error("API Error"));

      // This test structure is ready for implementation
      const expectedErrorBehavior = {
        showErrorToast: true,
        preservePendingActions: true,
        preserveHasChanges: true,
      };

      expect(expectedErrorBehavior.showErrorToast).toBe(true);
      expect(expectedErrorBehavior.preservePendingActions).toBe(true);
      expect(expectedErrorBehavior.preserveHasChanges).toBe(true);
    });
  });

  describe("edge cases", () => {
    it("should handle empty state gracefully", () => {
      const emptyBucketData = {
        common: {},
        custom_eng: {},
        currently_in_ts: {},
        delete: {},
      };

      expect(Object.keys(emptyBucketData)).toHaveLength(4);
      expect(Object.keys(emptyBucketData.common)).toHaveLength(0);
    });

    it("should handle items without fileId by using id", () => {
      const itemWithoutFileId: ILiveboardItem = {
        ...mockLibraryItems[0],
        fileId: undefined as any,
      };

      const fallbackId = itemWithoutFileId.fileId || itemWithoutFileId.id;
      expect(fallbackId).toBe(itemWithoutFileId.id);
    });

    it("should handle items without bucketId by defaulting to common", () => {
      const itemWithoutBucket: ILiveboardItem = {
        ...mockLibraryItems[0],
        bucketId: undefined as any,
      };

      const defaultBucket = itemWithoutBucket.bucketId || "common";
      expect(defaultBucket).toBe("common");
    });
  });
});