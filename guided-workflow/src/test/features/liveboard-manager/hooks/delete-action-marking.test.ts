import { act, renderHook } from "@testing-library/react";
import { toast } from "sonner";

import { useLiveboardManager } from "~/features/liveboard-manager/hooks/useLiveboardManager";
import type { ILiveboardItem } from "~/features/liveboard-manager/types";
import { createTestQueryClient, createWrapper } from "~/test/utils/test-utils";

// Mock toast notifications
jest.mock("sonner", () => ({
  toast: {
    success: jest.fn(),
    error: jest.fn(),
    info: jest.fn(),
  },
}));

// Mock TML API
jest.mock("~/api/tml", () => ({
  getTml: jest.fn(),
}));

describe("useLiveboardManager - Delete Action Marking", () => {
  const mockEngagementId = 123;
  const mockCanvasId = 456;

  let queryClient: ReturnType<typeof createTestQueryClient>;
  let wrapper: ReturnType<typeof createWrapper>;

  const mockStandardItem: ILiveboardItem = {
    id: "standard-item-1",
    fileId: "file-standard-1",
    display_name: "Standard Dashboard",
    bucketId: "common",
    category: "standard",
    isInWorkspace: false,
    isExisting: true,
  };

  const mockEngagementItem: ILiveboardItem = {
    id: "engagement-item-1",
    fileId: "file-engagement-1",
    display_name: "Engagement Dashboard",
    bucketId: "custom_eng",
    category: "engagement",
    isInWorkspace: false,
    isExisting: true,
  };

  const mockWorkspaceItem: ILiveboardItem = {
    id: "workspace-item-1",
    fileId: "file-workspace-1",
    display_name: "Workspace Dashboard",
    bucketId: "currently_in_ts",
    category: "engagement",
    isInWorkspace: true,
    isExisting: true,
  };

  beforeEach(() => {
    queryClient = createTestQueryClient();
    wrapper = createWrapper(queryClient);
    jest.clearAllMocks();
  });

  describe("delete action for library items", () => {
    it("should prevent deletion of standard category items", () => {
      const { result } = renderHook(
        () =>
          useLiveboardManager({
            engagementId: mockEngagementId,
            canvasId: mockCanvasId,
          }),
        { wrapper }
      );

      act(() => {
        result.current.deleteItem(mockStandardItem);
      });

      // Should show error toast
      expect(toast.error).toHaveBeenCalledWith(
        "Standard templates cannot be deleted"
      );

      // Should not add delete action
      expect(result.current.pendingActions).toHaveLength(0);

      // Should not mark item as deleted
      expect(
        result.current.libraryItems.find(
          (item) => item.id === mockStandardItem.id
        )?.isDeleted
      ).toBeFalsy();
    });

    it("should mark engagement category items as deleted", () => {
      const { result } = renderHook(
        () =>
          useLiveboardManager({
            engagementId: mockEngagementId,
            canvasId: mockCanvasId,
          }),
        { wrapper }
      );

      // First add the item to library items
      act(() => {
        result.current.libraryItems.push(mockEngagementItem);
      });

      act(() => {
        result.current.deleteItem(mockEngagementItem);
      });

      // Should mark item as deleted in library
      const deletedItem = result.current.libraryItems.find(
        (item) =>
          item.id === mockEngagementItem.id ||
          item.fileId === mockEngagementItem.fileId
      );
      expect(deletedItem?.isDeleted).toBe(true);

      // Should add delete action
      const deleteAction = result.current.pendingActions.find(
        (action) => action.type === "delete"
      );
      expect(deleteAction).toBeDefined();
      expect(deleteAction?.item.id).toBe(mockEngagementItem.id);
      expect(deleteAction?.context).toBe("library");

      // Should show success toast
      expect(toast.success).toHaveBeenCalledWith(
        "Marked 'Engagement Dashboard' for deletion"
      );
    });

    it("should preserve other item properties when marking as deleted", () => {
      const { result } = renderHook(
        () =>
          useLiveboardManager({
            engagementId: mockEngagementId,
            canvasId: mockCanvasId,
          }),
        { wrapper }
      );

      // Add item to library
      act(() => {
        result.current.libraryItems.push(mockEngagementItem);
      });

      const originalProperties = {
        id: mockEngagementItem.id,
        fileId: mockEngagementItem.fileId,
        display_name: mockEngagementItem.display_name,
        bucketId: mockEngagementItem.bucketId,
        category: mockEngagementItem.category,
        isInWorkspace: mockEngagementItem.isInWorkspace,
        isExisting: mockEngagementItem.isExisting,
      };

      act(() => {
        result.current.deleteItem(mockEngagementItem);
      });

      const deletedItem = result.current.libraryItems.find(
        (item) => item.id === mockEngagementItem.id
      );

      expect(deletedItem).toMatchObject({
        ...originalProperties,
        isDeleted: true,
      });
    });
  });

  describe("delete action for workspace items", () => {
    it("should mark workspace items as deleted instead of removing them", () => {
      const { result } = renderHook(
        () =>
          useLiveboardManager({
            engagementId: mockEngagementId,
            canvasId: mockCanvasId,
          }),
        { wrapper }
      );

      // Add item to workspace
      act(() => {
        result.current.workspaceItems.push(mockWorkspaceItem);
      });

      act(() => {
        result.current.removeFromWorkspace(mockWorkspaceItem);
      });

      // Should mark item as deleted (not remove it)
      const deletedItem = result.current.workspaceItems.find(
        (item) => item.id === mockWorkspaceItem.id
      );
      expect(deletedItem?.isDeleted).toBe(true);

      // Should add delete action
      const deleteAction = result.current.pendingActions.find(
        (action) => action.type === "delete"
      );
      expect(deleteAction).toBeDefined();
      expect(deleteAction?.context).toBe("workspace");
    });

    it("should completely remove new workspace items (not existing)", () => {
      const newWorkspaceItem: ILiveboardItem = {
        ...mockWorkspaceItem,
        isExisting: false, // New item, not from API
      };

      const { result } = renderHook(
        () =>
          useLiveboardManager({
            engagementId: mockEngagementId,
            canvasId: mockCanvasId,
          }),
        { wrapper }
      );

      // Add new item to workspace
      act(() => {
        result.current.workspaceItems.push(newWorkspaceItem);
      });

      act(() => {
        result.current.removeFromWorkspace(newWorkspaceItem);
      });

      // Should completely remove new item
      const removedItem = result.current.workspaceItems.find(
        (item) => item.id === newWorkspaceItem.id
      );
      expect(removedItem).toBeUndefined();

      // Should add remove action (not delete)
      const removeAction = result.current.pendingActions.find(
        (action) => action.type === "remove"
      );
      expect(removeAction).toBeDefined();
    });
  });

  describe("delete action tracking", () => {
    it("should create proper delete action with timestamp", () => {
      const { result } = renderHook(
        () =>
          useLiveboardManager({
            engagementId: mockEngagementId,
            canvasId: mockCanvasId,
          }),
        { wrapper }
      );

      act(() => {
        result.current.libraryItems.push(mockEngagementItem);
      });

      const beforeTime = Date.now();

      act(() => {
        result.current.deleteItem(mockEngagementItem);
      });

      const afterTime = Date.now();

      const deleteAction = result.current.pendingActions.find(
        (action) => action.type === "delete"
      );
      expect(deleteAction).toMatchObject({
        type: "delete",
        item: mockEngagementItem,
        context: "library",
      });
      expect(deleteAction?.timestamp).toBeGreaterThanOrEqual(beforeTime);
      expect(deleteAction?.timestamp).toBeLessThanOrEqual(afterTime);
      expect(deleteAction?.id).toMatch(/^delete_engagement-item-1_\d+$/);
    });

    it("should mark hasChanges as true after delete action", () => {
      const { result } = renderHook(
        () =>
          useLiveboardManager({
            engagementId: mockEngagementId,
            canvasId: mockCanvasId,
          }),
        { wrapper }
      );

      act(() => {
        result.current.libraryItems.push(mockEngagementItem);
      });

      expect(result.current.hasChanges).toBe(false);

      act(() => {
        result.current.deleteItem(mockEngagementItem);
      });

      expect(result.current.hasChanges).toBe(true);
    });
  });

  describe("save mutation with delete actions", () => {
    it("should move deleted items to delete bucket in save mutation", async () => {
      const { result } = renderHook(
        () =>
          useLiveboardManager({
            engagementId: mockEngagementId,
            canvasId: mockCanvasId,
          }),
        { wrapper }
      );

      act(() => {
        result.current.libraryItems.push(mockEngagementItem);
      });

      act(() => {
        result.current.deleteItem(mockEngagementItem);
      });

      const consoleSpy = jest.spyOn(console, "log").mockImplementation();

      await act(async () => {
        await result.current.saveChanges();
      });

      expect(consoleSpy).toHaveBeenCalledWith(
        "Save successful: ",
        expect.objectContaining({
          delete: expect.objectContaining({
            "file-engagement-1": {
              lb_params: {
                display_name: "Engagement Dashboard",
              },
            },
          }),
        })
      );

      consoleSpy.mockRestore();
    });

    it("should remove deleted items from their original bucket", async () => {
      const { result } = renderHook(
        () =>
          useLiveboardManager({
            engagementId: mockEngagementId,
            canvasId: mockCanvasId,
          }),
        { wrapper }
      );

      act(() => {
        result.current.libraryItems.push(mockEngagementItem);
      });

      act(() => {
        result.current.deleteItem(mockEngagementItem);
      });

      const consoleSpy = jest.spyOn(console, "log").mockImplementation();

      await act(async () => {
        await result.current.saveChanges();
      });

      // Should not be in custom_eng bucket anymore
      expect(consoleSpy).toHaveBeenCalledWith(
        "Save successful: ",
        expect.objectContaining({
          custom_eng: expect.not.objectContaining({
            "file-engagement-1": expect.anything(),
          }),
        })
      );

      consoleSpy.mockRestore();
    });
  });

  describe("edge cases", () => {
    it("should handle delete action for non-existent item gracefully", () => {
      const nonExistentItem: ILiveboardItem = {
        id: "non-existent",
        fileId: "file-non-existent",
        display_name: "Non-existent Item",
        bucketId: "custom_eng",
        category: "engagement",
        isInWorkspace: false,
        isExisting: true,
      };

      const { result } = renderHook(
        () =>
          useLiveboardManager({
            engagementId: mockEngagementId,
            canvasId: mockCanvasId,
          }),
        { wrapper }
      );

      expect(() => {
        act(() => {
          result.current.deleteItem(nonExistentItem);
        });
      }).not.toThrow();

      // Should still add the action
      expect(result.current.pendingActions).toHaveLength(1);
    });

    it("should handle multiple delete actions for the same item", () => {
      const { result } = renderHook(
        () =>
          useLiveboardManager({
            engagementId: mockEngagementId,
            canvasId: mockCanvasId,
          }),
        { wrapper }
      );

      act(() => {
        result.current.libraryItems.push(mockEngagementItem);
      });

      act(() => {
        result.current.deleteItem(mockEngagementItem);
        result.current.deleteItem(mockEngagementItem);
      });

      // Should have two delete actions
      const deleteActions = result.current.pendingActions.filter(
        (action) => action.type === "delete"
      );
      expect(deleteActions).toHaveLength(2);
    });
  });
});
