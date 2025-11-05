import { describe, expect, it } from "vitest";

import type { ILiveboardItem } from "~/features/liveboard-manager/types";

describe("Enhanced ILiveboardItem Interface", () => {
  const mockBaseItem: ILiveboardItem = {
    fileId: "test-file-id",
    ephemeral: false,
    display_name: "Test Liveboard",
    bucketId: "currently_in_ts",
    parent_id: null,
    originalBucket: null,
    id: "test-id",
    category: "engagement",
  };

  describe("isDeleted flag", () => {
    it("should support isDeleted as optional boolean property", () => {
      const deletedItem: ILiveboardItem = {
        ...mockBaseItem,
        isDeleted: true,
      };

      expect(deletedItem.isDeleted).toBe(true);
      expect(typeof deletedItem.isDeleted).toBe("boolean");
    });

    it("should default to undefined when isDeleted is not set", () => {
      const normalItem: ILiveboardItem = {
        ...mockBaseItem,
      };

      expect(normalItem.isDeleted).toBeUndefined();
    });

    it("should support false value for isDeleted", () => {
      const activeItem: ILiveboardItem = {
        ...mockBaseItem,
        isDeleted: false,
      };

      expect(activeItem.isDeleted).toBe(false);
    });
  });

  describe("isExisting flag", () => {
    it("should support isExisting as optional boolean property", () => {
      const existingItem: ILiveboardItem = {
        ...mockBaseItem,
        isExisting: true,
      };

      expect(existingItem.isExisting).toBe(true);
      expect(typeof existingItem.isExisting).toBe("boolean");
    });

    it("should default to undefined when isExisting is not set", () => {
      const newItem: ILiveboardItem = {
        ...mockBaseItem,
      };

      expect(newItem.isExisting).toBeUndefined();
    });

    it("should support false value for isExisting", () => {
      const newItem: ILiveboardItem = {
        ...mockBaseItem,
        isExisting: false,
      };

      expect(newItem.isExisting).toBe(false);
    });
  });

  describe("combined state flags", () => {
    it("should support both isDeleted and isExisting flags together", () => {
      const deletedExistingItem: ILiveboardItem = {
        ...mockBaseItem,
        isDeleted: true,
        isExisting: true,
      };

      expect(deletedExistingItem.isDeleted).toBe(true);
      expect(deletedExistingItem.isExisting).toBe(true);
    });

    it("should support all existing properties along with new flags", () => {
      const fullItem: ILiveboardItem = {
        ...mockBaseItem,
        isInWorkspace: true,
        isLoading: false,
        isDeleted: false,
        isExisting: true,
      };

      expect(fullItem.isInWorkspace).toBe(true);
      expect(fullItem.isLoading).toBe(false);
      expect(fullItem.isDeleted).toBe(false);
      expect(fullItem.isExisting).toBe(true);
      expect(fullItem.category).toBe("engagement");
      expect(fullItem.display_name).toBe("Test Liveboard");
    });
  });

  describe("category property", () => {
    it("should support standard category", () => {
      const standardItem: ILiveboardItem = {
        ...mockBaseItem,
        category: "standard",
      };

      expect(standardItem.category).toBe("standard");
    });

    it("should support engagement category", () => {
      const engagementItem: ILiveboardItem = {
        ...mockBaseItem,
        category: "engagement",
      };

      expect(engagementItem.category).toBe("engagement");
    });
  });

  describe("state combinations for different scenarios", () => {
    it("should represent a new workspace item correctly", () => {
      const newWorkspaceItem: ILiveboardItem = {
        ...mockBaseItem,
        isInWorkspace: true,
        isExisting: false,
        isDeleted: false,
      };

      expect(newWorkspaceItem.isInWorkspace).toBe(true);
      expect(newWorkspaceItem.isExisting).toBe(false);
      expect(newWorkspaceItem.isDeleted).toBe(false);
    });

    it("should represent an existing deleted item correctly", () => {
      const deletedExistingItem: ILiveboardItem = {
        ...mockBaseItem,
        isInWorkspace: true,
        isExisting: true,
        isDeleted: true,
      };

      expect(deletedExistingItem.isInWorkspace).toBe(true);
      expect(deletedExistingItem.isExisting).toBe(true);
      expect(deletedExistingItem.isDeleted).toBe(true);
    });

    it("should represent a library item correctly", () => {
      const libraryItem: ILiveboardItem = {
        ...mockBaseItem,
        isInWorkspace: false,
        isExisting: true,
        isDeleted: false,
        category: "standard",
      };

      expect(libraryItem.isInWorkspace).toBe(false);
      expect(libraryItem.isExisting).toBe(true);
      expect(libraryItem.isDeleted).toBe(false);
      expect(libraryItem.category).toBe("standard");
    });
  });
});
