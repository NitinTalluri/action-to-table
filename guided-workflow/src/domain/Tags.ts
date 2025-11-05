import { z } from "zod";

export const TagSchema = z.object({
  tag_desc: z.string(),
  tag_id: z.number(),
  tag_name: z.string(),
  tagset_id: z.number(),
});

export type TTag = z.infer<typeof TagSchema>;

export const TagRequestSchema = z.object({
  tag_name: z.string().min(1),
  tag_desc: z.string(),
  tagset_id: z.coerce.number(),
});

export type TTagRequest = z.infer<typeof TagRequestSchema>;

export const DeletedTagSchema = z.object({
  cardinality: z.string(),
  dc_engagement_id: z.number(),
  scope: z.union([z.literal("Engagement"), z.literal("Global")]),
  tag_desc: z.string().nullish(),
  tag_id: z.number(),
  tag_name: z.coerce.string(),
  tagset_id: z.number(),
  tagset_name: z.number(),
  tagset_type: z.number(),
  update_dtm: z.string(),
  updated_by: z.string(),
});

export type TDeletedTag = z.infer<typeof DeletedTagSchema>;
