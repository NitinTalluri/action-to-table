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

describe("useLiveboardManager - Save as Template Functionality", () => {
  const mockEngagementId = 123;
  const mockCanvasId = 456;

  let queryClient: ReturnType<typeof createTestQueryClient>;
  let wrapper: ReturnType<typeof createWrapper>;

  const mockWorkspaceItem: ILiveboardItem = {
    id: "workspace-item-1",
    fileId: "file-workspace-1",
    display_name: "Workspace Dashboard",
    bucketId: "currently_in_ts",
    category: "engagement",
    isInWorkspace: true,
    isExisting: true,
  };

  const mockLibraryItem: ILiveboardItem = {
    id: "library-item-1",
    fileId: "file-library-1",
    display_name: "Library Dashboard",
    bucketId: "custom_eng",
    category: "engagement",
    isInWorkspace: false,
    isExisting: true,
  };

  beforeEach(() => {
    queryClient = createTestQueryClient();
    wrapper = createWrapper(queryClient);
    jest.clearAllMocks();
  });

  describe("saveAsTemplate action", () => {
    it("should add save-as-template action for workspace item", () => {
      const { result } = renderHook(
        () =>
          useLiveboardManager({
            engagementId: mockEngagementId,
            canvasId: mockCanvasId,
          }),
        { wrapper }
      );

      act(() => {
        result.current.saveAsTemplate(mockWorkspaceItem);
      });

      // Check that action was added to pending actions
      const actions = result.current.pendingActions;
      expect(actions).toHaveLength(1);
      expect(actions[0]).toMatchObject({
        type: "save-as-template",
        item: mockWorkspaceItem,
      });
      expect(actions[0].id).toMatch(/^save-as-template_workspace-item-1_\d+$/);
      expect(actions[0].timestamp).toBeGreaterThan(0);
    });

    it("should add save-as-template action for library item", () => {
      const { result } = renderHook(
        () =>
          useLiveboardManager({
            engagementId: mockEngagementId,
            canvasId: mockCanvasId,
          }),
        { wrapper }
      );

      act(() => {
        result.current.saveAsTemplate(mockLibraryItem);
      });

      // Check that action was added to pending actions
      const actions = result.current.pendingActions;
      expect(actions).toHaveLength(1);
      expect(actions[0]).toMatchObject({
        type: "save-as-template",
        item: mockLibraryItem,
      });
      expect(actions[0].id).toMatch(/^save-as-template_library-item-1_\d+$/);
      expect(actions[0].timestamp).toBeGreaterThan(0);
    });

    it("should mark hasChanges as true after save-as-template action", () => {
      const { result } = renderHook(
        () =>
          useLiveboardManager({
            engagementId: mockEngagementId,
            canvasId: mockCanvasId,
          }),
        { wrapper }
      );

      expect(result.current.hasChanges).toBe(false);

      act(() => {
        result.current.saveAsTemplate(mockWorkspaceItem);
      });

      expect(result.current.hasChanges).toBe(true);
    });

    it("should show success toast notification", () => {
      const { result } = renderHook(
        () =>
          useLiveboardManager({
            engagementId: mockEngagementId,
            canvasId: mockCanvasId,
          }),
        { wrapper }
      );

      act(() => {
        result.current.saveAsTemplate(mockWorkspaceItem);
      });

      expect(toast.success).toHaveBeenCalledWith(
        "'Workspace Dashboard' will be saved as template on save"
      );
    });

    it("should handle multiple save-as-template actions", () => {
      const { result } = renderHook(
        () =>
          useLiveboardManager({
            engagementId: mockEngagementId,
            canvasId: mockCanvasId,
          }),
        { wrapper }
      );

      act(() => {
        result.current.saveAsTemplate(mockWorkspaceItem);
        result.current.saveAsTemplate(mockLibraryItem);
      });

      const actions = result.current.pendingActions;
      expect(actions).toHaveLength(2);
      expect(actions[0].type).toBe("save-as-template");
      expect(actions[1].type).toBe("save-as-template");
      expect(actions[0].item.id).toBe("workspace-item-1");
      expect(actions[1].item.id).toBe("library-item-1");
    });

    it("should generate unique action IDs for multiple save-as-template actions", () => {
      const { result } = renderHook(
        () =>
          useLiveboardManager({
            engagementId: mockEngagementId,
            canvasId: mockCanvasId,
          }),
        { wrapper }
      );

      act(() => {
        result.current.saveAsTemplate(mockWorkspaceItem);
      });

      // Wait a bit to ensure different timestamp
      setTimeout(() => {
        act(() => {
          result.current.saveAsTemplate(mockWorkspaceItem);
        });
      }, 10);

      const actions = result.current.pendingActions;
      expect(actions).toHaveLength(2);
      expect(actions[0].id).not.toBe(actions[1].id);
    });
  });

  describe("save mutation with save-as-template actions", () => {
    it("should process save-as-template action in save mutation", async () => {
      const { result } = renderHook(
        () =>
          useLiveboardManager({
            engagementId: mockEngagementId,
            canvasId: mockCanvasId,
          }),
        { wrapper }
      );

      // Add save-as-template action
      act(() => {
        result.current.saveAsTemplate(mockWorkspaceItem);
      });

      // Mock console.log to capture save payload
      const consoleSpy = jest.spyOn(console, "log").mockImplementation();

      // Trigger save
      await act(async () => {
        await result.current.saveChanges();
      });

      // Verify console.log was called with bucket data
      expect(consoleSpy).toHaveBeenCalledWith(
        "Save successful: ",
        expect.objectContaining({
          custom_eng: expect.objectContaining({
            [`file-workspace-1_template_${expect.any(Number)}`]: {
              lb_params: {
                display_name: "Workspace Dashboard (Template)",
              },
            },
          }),
        })
      );

      consoleSpy.mockRestore();
    });

    it("should assign save-as-template items to custom_eng bucket", async () => {
      const { result } = renderHook(
        () =>
          useLiveboardManager({
            engagementId: mockEngagementId,
            canvasId: mockCanvasId,
          }),
        { wrapper }
      );

      act(() => {
        result.current.saveAsTemplate(mockLibraryItem);
      });

      const consoleSpy = jest.spyOn(console, "log").mockImplementation();

      await act(async () => {
        await result.current.saveChanges();
      });

      expect(consoleSpy).toHaveBeenCalledWith(
        "Save successful: ",
        expect.objectContaining({
          custom_eng: expect.objectContaining({
            [`file-library-1_template_${expect.any(Number)}`]: {
              lb_params: {
                display_name: "Library Dashboard (Template)",
              },
            },
          }),
        })
      );

      consoleSpy.mockRestore();
    });

    it("should append (Template) suffix to display name", async () => {
      const { result } = renderHook(
        () =>
          useLiveboardManager({
            engagementId: mockEngagementId,
            canvasId: mockCanvasId,
          }),
        { wrapper }
      );

      const itemWithLongName: ILiveboardItem = {
        ...mockWorkspaceItem,
        display_name: "Very Long Dashboard Name for Testing",
      };

      act(() => {
        result.current.saveAsTemplate(itemWithLongName);
      });

      const consoleSpy = jest.spyOn(console, "log").mockImplementation();

      await act(async () => {
        await result.current.saveChanges();
      });

      expect(consoleSpy).toHaveBeenCalledWith(
        "Save successful: ",
        expect.objectContaining({
          custom_eng: expect.objectContaining({
            [`file-workspace-1_template_${expect.any(Number)}`]: {
              lb_params: {
                display_name: "Very Long Dashboard Name for Testing (Template)",
              },
            },
          }),
        })
      );

      consoleSpy.mockRestore();
    });

    it("should clear pending actions after successful save", async () => {
      const { result } = renderHook(
        () =>
          useLiveboardManager({
            engagementId: mockEngagementId,
            canvasId: mockCanvasId,
          }),
        { wrapper }
      );

      act(() => {
        result.current.saveAsTemplate(mockWorkspaceItem);
      });

      expect(result.current.pendingActions).toHaveLength(1);

      await act(async () => {
        await result.current.saveChanges();
      });

      expect(result.current.pendingActions).toHaveLength(0);
      expect(result.current.hasChanges).toBe(false);
    });

    it("should show success toast after save completion", async () => {
      const { result } = renderHook(
        () =>
          useLiveboardManager({
            engagementId: mockEngagementId,
            canvasId: mockCanvasId,
          }),
        { wrapper }
      );

      act(() => {
        result.current.saveAsTemplate(mockWorkspaceItem);
      });

      await act(async () => {
        await result.current.saveChanges();
      });

      expect(toast.success).toHaveBeenCalledWith("Changes saved successfully");
    });
  });

  describe("edge cases", () => {
    it("should handle save-as-template for item without fileId", () => {
      const itemWithoutFileId: ILiveboardItem = {
        ...mockWorkspaceItem,
        fileId: undefined,
      };

      const { result } = renderHook(
        () =>
          useLiveboardManager({
            engagementId: mockEngagementId,
            canvasId: mockCanvasId,
          }),
        { wrapper }
      );

      act(() => {
        result.current.saveAsTemplate(itemWithoutFileId);
      });

      const actions = result.current.pendingActions;
      expect(actions).toHaveLength(1);
      expect(actions[0].type).toBe("save-as-template");
      expect(actions[0].item).toBe(itemWithoutFileId);
    });

    it("should handle save-as-template for item with empty display name", () => {
      const itemWithEmptyName: ILiveboardItem = {
        ...mockWorkspaceItem,
        display_name: "",
      };

      const { result } = renderHook(
        () =>
          useLiveboardManager({
            engagementId: mockEngagementId,
            canvasId: mockCanvasId,
          }),
        { wrapper }
      );

      act(() => {
        result.current.saveAsTemplate(itemWithEmptyName);
      });

      expect(toast.success).toHaveBeenCalledWith(
        "'' will be saved as template on save"
      );
    });
  });
});
