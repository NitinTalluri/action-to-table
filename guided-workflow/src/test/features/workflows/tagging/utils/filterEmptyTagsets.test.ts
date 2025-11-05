import { describe, expect, it } from "vitest";

import { TTagset } from "~/domain/Tagset";
import { filterEmptyTagsets } from "~/features/workflows/tagging/utils/filterEmptyTagsets";

describe("filterEmptyTagsets Utility", () => {
  // Arrange: Set up test data
  const mockTagsets: TTagset[] = [
    {
      tagset_id: 1,
      tagset_name: "Empty Tagset",
      tagset_desc: "Empty tagset description",
      cardinality: "single",
      tagset_type: 1,
      scope: "Engagement",
      dc_engagement_id: 1,
      tags: [],
    },
    {
      tagset_id: 2,
      tagset_name: "Non-Empty Tagset",
      tagset_desc: "Non-empty tagset description",
      cardinality: "single",
      tagset_type: 1,
      scope: "Engagement",
      dc_engagement_id: 1,
      tags: [
        {
          tag_id: 1,
          tag_name: "Tag 1",
          tag_desc: "Tag 1 description",
          tagset_id: 2,
        },
      ],
    },
    {
      tagset_id: 3,
      tagset_name: "Global Empty",
      tagset_desc: "Global empty tagset description",
      cardinality: "single",
      tagset_type: 1,
      scope: "Global",
      tags: [],
    },
    {
      tagset_id: 4,
      tagset_name: "Global Non-Empty",
      tagset_desc: "Global non-empty tagset description",
      cardinality: "single",
      tagset_type: 1,
      scope: "Global",
      tags: [
        {
          tag_id: 2,
          tag_name: "Tag 2",
          tag_desc: "Tag 2 description",
          tagset_id: 4,
        },
      ],
    },
  ];

  it("should filter out tagsets with empty tags array", () => {
    // Act: Call the function with mixed empty and non-empty tagsets
    const result = filterEmptyTagsets(mockTagsets);

    // Assert: Only non-empty tagsets should be returned
    expect(result).toHaveLength(2);
    expect(result.map((ts) => ts.tagset_name)).toEqual([
      "Non-Empty Tagset",
      "Global Non-Empty",
    ]);
  });

  it("should return empty array when input is null", () => {
    // Act: Call function with null input
    const result = filterEmptyTagsets(null);

    // Assert: Should return empty array
    expect(result).toEqual([]);
  });

  it("should return empty array when all tagsets have no tags", () => {
    // Arrange: Create tagsets with only empty tags arrays
    const emptyTagsets: TTagset[] = [
      {
        tagset_id: 1,
        tagset_name: "Empty 1",
        tagset_desc: "Empty description",
        cardinality: "single",
        tagset_type: 1,
        scope: "Engagement",
        dc_engagement_id: 1,
        tags: [],
      },
      {
        tagset_id: 2,
        tagset_name: "Empty 2",
        tagset_desc: "Empty description",
        cardinality: "single",
        tagset_type: 1,
        scope: "Global",
        tags: [],
      },
    ];

    // Act: Filter the empty tagsets
    const result = filterEmptyTagsets(emptyTagsets);

    // Assert: Should return empty array
    expect(result).toEqual([]);
  });

  it("should return all tagsets when none have empty tags", () => {
    // Arrange: Create tagsets that all have tags
    const nonEmptyTagsets: TTagset[] = [
      {
        tagset_id: 1,
        tagset_name: "Valid 1",
        tagset_desc: "Valid description",
        cardinality: "single",
        tagset_type: 1,
        scope: "Engagement",
        dc_engagement_id: 1,
        tags: [
          {
            tag_id: 1,
            tag_name: "Tag 1",
            tag_desc: "Tag 1 description",
            tagset_id: 1,
          },
        ],
      },
      {
        tagset_id: 2,
        tagset_name: "Valid 2",
        tagset_desc: "Valid description",
        cardinality: "single",
        tagset_type: 1,
        scope: "Global",
        tags: [
          {
            tag_id: 2,
            tag_name: "Tag 2",
            tag_desc: "Tag 2 description",
            tagset_id: 2,
          },
        ],
      },
    ];

    // Act: Filter the non-empty tagsets
    const result = filterEmptyTagsets(nonEmptyTagsets);

    // Assert: Should return all tagsets unchanged
    expect(result).toHaveLength(2);
    expect(result).toEqual(nonEmptyTagsets);
  });

  it("should handle empty array input", () => {
    // Act: Call function with empty array
    const result = filterEmptyTagsets([]);

    // Assert: Should return empty array
    expect(result).toEqual([]);
  });
});
