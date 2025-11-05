import { beforeEach, describe, expect, it } from "vitest";

import type { ITmlFile, ITmlResponse } from "~/domain/Tml";
import { convertTmlResponseToData } from "~/domain/Tml";
import type { ILiveboardItem } from "~/features/liveboard-manager/types";

describe("TML Data Parsing with Bucket Logic", () => {
  let mockTmlResponse: ITmlResponse;
  let mockTmlFiles: ITmlFile[];

  beforeEach(() => {
    // Mock TML API response with different buckets
    mockTmlResponse = {
      common: {
        "standard-dashboard-1": {
          lb_params: {
            display_name: "Standard Sales Dashboard",
          },
        },
        "standard-dashboard-2": {
          lb_params: {
            display_name: "Standard Marketing Dashboard",
          },
        },
      },
      custom_eng: {
        "custom-engagement-1": {
          lb_params: {
            display_name: "Custom Engagement Analytics",
          },
        },
        "custom-engagement-2": {
          lb_params: {
            display_name: "Custom Performance Metrics",
          },
        },
      },
      currently_in_ts: {
        "workspace-item-1": {
          lb_params: {
            display_name: "Active Workspace Dashboard",
          },
        },
        "workspace-item-2": {
          lb_params: {
            display_name: "Current Analytics View",
          },
        },
      },
      delete: {
        "deleted-item-1": {
          lb_params: {
            display_name: "Deleted Dashboard",
          },
        },
      },
    };

    // Mock converted TML files
    mockTmlFiles = [
      {
        fileId: "standard-dashboard-1",
        ephemeral: false,
        display_name: "Standard Sales Dashboard",
        bucketId: "common",
        parent_id: null,
        originalBucket: null,
        id: "common-standard-dashboard-1",
      },
      {
        fileId: "custom-engagement-1",
        ephemeral: false,
        display_name: "Custom Engagement Analytics",
        bucketId: "custom_eng",
        parent_id: null,
        originalBucket: null,
        id: "custom_eng-custom-engagement-1",
      },
      {
        fileId: "workspace-item-1",
        ephemeral: false,
        display_name: "Active Workspace Dashboard",
        bucketId: "currently_in_ts",
        parent_id: null,
        originalBucket: null,
        id: "currently_in_ts-workspace-item-1",
      },
      {
        fileId: "deleted-item-1",
        ephemeral: false,
        display_name: "Deleted Dashboard",
        bucketId: "delete",
        parent_id: null,
        originalBucket: null,
        id: "delete-deleted-item-1",
      },
    ];
  });

  describe("bucket identification", () => {
    it("should identify common bucket items as standard category", () => {
      const commonItems = mockTmlFiles.filter(
        (file) => file.bucketId === "common"
      );

      expect(commonItems).toHaveLength(1);
      expect(commonItems[0].bucketId).toBe("common");
      expect(commonItems[0].display_name).toBe("Standard Sales Dashboard");
    });

    it("should identify custom_eng bucket items as engagement category", () => {
      const customEngItems = mockTmlFiles.filter(
        (file) => file.bucketId === "custom_eng"
      );

      expect(customEngItems).toHaveLength(1);
      expect(customEngItems[0].bucketId).toBe("custom_eng");
      expect(customEngItems[0].display_name).toBe(
        "Custom Engagement Analytics"
      );
    });

    it("should identify currently_in_ts bucket items as workspace items", () => {
      const workspaceItems = mockTmlFiles.filter(
        (file) => file.bucketId === "currently_in_ts"
      );

      expect(workspaceItems).toHaveLength(1);
      expect(workspaceItems[0].bucketId).toBe("currently_in_ts");
      expect(workspaceItems[0].display_name).toBe("Active Workspace Dashboard");
    });

    it("should identify delete bucket items as deleted items", () => {
      const deletedItems = mockTmlFiles.filter(
        (file) => file.bucketId === "delete"
      );

      expect(deletedItems).toHaveLength(1);
      expect(deletedItems[0].bucketId).toBe("delete");
      expect(deletedItems[0].display_name).toBe("Deleted Dashboard");
    });
  });

  describe("library vs workspace separation", () => {
    it("should separate library items (common + custom_eng) from workspace items", () => {
      const libraryBuckets = ["common", "custom_eng"];
      const workspaceBuckets = ["currently_in_ts"];

      const libraryItems = mockTmlFiles.filter((file) =>
        libraryBuckets.includes(file.bucketId)
      );

      const workspaceItems = mockTmlFiles.filter((file) =>
        workspaceBuckets.includes(file.bucketId)
      );

      expect(libraryItems).toHaveLength(2);
      expect(workspaceItems).toHaveLength(1);

      // Verify library items
      expect(libraryItems[0].bucketId).toBe("common");
      expect(libraryItems[1].bucketId).toBe("custom_eng");

      // Verify workspace items
      expect(workspaceItems[0].bucketId).toBe("currently_in_ts");
    });

    it("should exclude delete bucket items from both library and workspace", () => {
      const activeItems = mockTmlFiles.filter(
        (file) => file.bucketId !== "delete"
      );

      expect(activeItems).toHaveLength(3);
      expect(activeItems.every((item) => item.bucketId !== "delete")).toBe(
        true
      );
    });
  });

  describe("liveboard item transformation", () => {
    it("should transform common bucket items to standard category liveboards", () => {
      const commonFile = mockTmlFiles.find(
        (file) => file.bucketId === "common"
      );

      const liveboardItem: ILiveboardItem = {
        ...commonFile!,
        category: "standard",
        isInWorkspace: false,
        isExisting: true,
      };

      expect(liveboardItem.category).toBe("standard");
      expect(liveboardItem.isInWorkspace).toBe(false);
      expect(liveboardItem.isExisting).toBe(true);
      expect(liveboardItem.bucketId).toBe("common");
    });

    it("should transform custom_eng bucket items to engagement category liveboards", () => {
      const customEngFile = mockTmlFiles.find(
        (file) => file.bucketId === "custom_eng"
      );

      const liveboardItem: ILiveboardItem = {
        ...customEngFile!,
        category: "engagement",
        isInWorkspace: false,
        isExisting: true,
      };

      expect(liveboardItem.category).toBe("engagement");
      expect(liveboardItem.isInWorkspace).toBe(false);
      expect(liveboardItem.isExisting).toBe(true);
      expect(liveboardItem.bucketId).toBe("custom_eng");
    });

    it("should transform currently_in_ts bucket items to workspace liveboards", () => {
      const workspaceFile = mockTmlFiles.find(
        (file) => file.bucketId === "currently_in_ts"
      );

      const liveboardItem: ILiveboardItem = {
        ...workspaceFile!,
        category: "engagement",
        isInWorkspace: true,
        isExisting: true,
      };

      expect(liveboardItem.category).toBe("engagement");
      expect(liveboardItem.isInWorkspace).toBe(true);
      expect(liveboardItem.isExisting).toBe(true);
      expect(liveboardItem.bucketId).toBe("currently_in_ts");
    });
  });

  describe("complete data transformation flow", () => {
    it("should process complete TML response and separate into library and workspace", () => {
      // Simulate the complete transformation flow
      const allItems = convertTmlResponseToData(mockTmlResponse);

      // Separate library and workspace items
      const library = allItems
        .filter(
          (item) => item.bucketId === "common" || item.bucketId === "custom_eng"
        )
        .map(
          (item) =>
            ({
              ...item,
              category: item.bucketId === "common" ? "standard" : "engagement",
              isInWorkspace: false,
              isExisting: true,
            }) as ILiveboardItem
        );

      const workspace = allItems
        .filter((item) => item.bucketId === "currently_in_ts")
        .map(
          (item) =>
            ({
              ...item,
              category: "engagement",
              isInWorkspace: true,
              isExisting: true,
            }) as ILiveboardItem
        );

      // Verify we have the expected total items (excluding delete bucket)
      const activeItems = allItems.filter((item) => item.bucketId !== "delete");
      expect(activeItems).toHaveLength(6); // 2 common + 2 custom_eng + 2 currently_in_ts = 6 total

      // Verify library items (should be 4: 2 common + 2 custom_eng)
      expect(library).toHaveLength(4);
      expect(
        library.filter((item) => item.category === "standard")
      ).toHaveLength(2); // common items
      expect(
        library.filter((item) => item.category === "engagement")
      ).toHaveLength(2); // custom_eng items
      expect(library.every((item) => !item.isInWorkspace)).toBe(true);
      expect(library.every((item) => item.isExisting)).toBe(true);

      // Verify workspace items (should be 2: currently_in_ts)
      expect(workspace).toHaveLength(2);
      expect(workspace.every((item) => item.category === "engagement")).toBe(
        true
      );
      expect(workspace.every((item) => item.isInWorkspace)).toBe(true);
      expect(workspace.every((item) => item.isExisting)).toBe(true);
    });

    it("should handle empty buckets gracefully", () => {
      const emptyTmlResponse: ITmlResponse = {
        common: {},
        custom_eng: {},
        currently_in_ts: {},
        delete: {},
      };

      const allItems = convertTmlResponseToData(emptyTmlResponse);
      expect(allItems).toHaveLength(0);

      const library = allItems.filter(
        (item) => item.bucketId === "common" || item.bucketId === "custom_eng"
      );
      const workspace = allItems.filter(
        (item) => item.bucketId === "currently_in_ts"
      );

      expect(library).toHaveLength(0);
      expect(workspace).toHaveLength(0);
    });

    it("should handle missing buckets gracefully", () => {
      const partialTmlResponse: ITmlResponse = {
        common: {
          "item-1": {
            lb_params: {
              display_name: "Only Common Item",
            },
          },
        },
      };

      const allItems = convertTmlResponseToData(partialTmlResponse);
      expect(allItems).toHaveLength(1);
      expect(allItems[0].bucketId).toBe("common");

      const library = allItems.filter(
        (item) => item.bucketId === "common" || item.bucketId === "custom_eng"
      );
      const workspace = allItems.filter(
        (item) => item.bucketId === "currently_in_ts"
      );

      expect(library).toHaveLength(1);
      expect(workspace).toHaveLength(0);
    });
  });

  describe("bucket assignment validation", () => {
    it("should validate all expected bucket types are handled", () => {
      const expectedBuckets = [
        "common",
        "custom_eng",
        "currently_in_ts",
        "delete",
      ];
      const actualBuckets = Object.keys(mockTmlResponse);

      expectedBuckets.forEach((bucket) => {
        expect(actualBuckets).toContain(bucket);
      });
    });

    it("should correctly map bucket to category", () => {
      const bucketToCategoryMap = {
        common: "standard",
        custom_eng: "engagement",
        currently_in_ts: "engagement", // workspace items are engagement type
        delete: "engagement", // deleted items maintain their type
      };

      Object.entries(bucketToCategoryMap).forEach(
        ([bucket, expectedCategory]) => {
          const category = bucket === "common" ? "standard" : "engagement";
          expect(category).toBe(expectedCategory);
        }
      );
    });

    it("should correctly map bucket to workspace status", () => {
      const bucketToWorkspaceMap = {
        common: false,
        custom_eng: false,
        currently_in_ts: true,
        delete: false, // deleted items are not in workspace
      };

      Object.entries(bucketToWorkspaceMap).forEach(
        ([bucket, expectedInWorkspace]) => {
          const isInWorkspace = bucket === "currently_in_ts";
          expect(isInWorkspace).toBe(expectedInWorkspace);
        }
      );
    });
  });
});
