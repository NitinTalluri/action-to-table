import { z } from "zod";

import { TagOption } from "~/domain/thoughtspot";

import { TIdType } from "./SnifReport";
import { TagSchema } from "./Tags";

export const TagsetRequestSchema = z.object({
  tagset_name: z.string(),
  tagset_desc: z.string(),
  scope: z.literal("Engagement"),
  cardinality: z.string(),
  tagset_type: z.coerce.number(),
  dc_engagement_id: z.coerce.number(),
});

export type TTagsetRequest = z.infer<typeof TagsetRequestSchema>;

export const DeletedTagsetResponseSchema = z.object({
  tagset_name: z.string(),
  tagset_desc: z.string(),
  scope: z.union([z.literal("Engagement"), z.literal("Global")]),
  cardinality: z.string(),
  tagset_type: z.coerce.number(),
  dc_engagement_id: z.coerce.number(),
  tagset_id: z.number(),
});

export type TDeletedTagsetResponse = z.infer<
  typeof DeletedTagsetResponseSchema
>;

export const TagsetGlobalRequestSchema = z.object({
  tagset_name: z.string(),
  tagset_desc: z.string(),
  scope: z.literal("Global"),
  cardinality: z.string(),
  tagset_type: z.coerce.number(),
});

export type TTagsetGlobalRequest = z.infer<typeof TagsetGlobalRequestSchema>;

export const TagsetBaseSchema = z.object({
  tagset_id: z.number(),
  tagset_desc: z.string(),
  cardinality: z.string(),
  tags: z.array(TagSchema).catch([]),
  tagset_name: z.string(),
  tagset_type: z.number(),
});

export const TagsetGlobalSchema = TagsetBaseSchema.extend({
  scope: z.literal("Global"),
});

export type TTagsetGlobal = z.infer<typeof TagsetGlobalSchema>;

export const TagsetEngagementSchema = TagsetBaseSchema.extend({
  dc_engagement_id: z.coerce.number(),
  scope: z.literal("Engagement"),
});

export type TTagsetEngagement = z.infer<typeof TagsetEngagementSchema>;

export type TTagset = TTagsetGlobal | TTagsetEngagement;

export type TEngagementTagsetResponse = TTagsetEngagement[];

export type TTagsetResponse = TTagset[];

export const isGlobalTagset = (ts: TTagset): ts is TTagsetGlobal => {
  return ts.scope === "Global";
};

export const TagSetGlobalResponseSchema = z.object({
  tagset_name: z.string(),
  tagset_desc: z.string(),
  scope: z.literal("Global"),
  cardinality: z.string(),
  tagset_type: z.number(),
  tagset_id: z.number(),
});

export type TTagsetGlobalResponse = z.infer<
  typeof TagSetGlobalResponseSchema
>[];

export const TagSetResponseSchema = z.object({
  tagset_name: z.string(),
  tagset_desc: z.string(),
  scope: z.union([z.literal("Engagement"), z.literal("Global")]),
  cardinality: z.string(),
  tagset_type: z.number(),
  dc_engagement_id: z.number(),
  tagset_id: z.number(),
});

export type BulkTaggingPayload = {
  id_type: TIdType;
  engagement_id: number;
  comment: string;
  row_data: {
    id: number | string;
    tagset_id: number;
    tag_name: string;
  }[];
  config_strategy: TagOption;
};

export const TagHistoryResponseSchema = z.object({
  external_job_id: z.string().uuid(),
  external_run_id: z.string().uuid(),
  message: z.string(),
  notification_id: z.number(),
  request_id: z.number(),
  success: z.boolean(),
});

export const TagHistoryRequestSchema = z.object({
  id_type: z.enum(["instance_id", "serial_number"]),
  ids: z.union([z.array(z.string()), z.array(z.number())]),
  engagement_id: z.number(),
  tagset_ids: z.array(z.number()),
  from_date: z
    .string()
    .regex(/^\d{4}-\d{2}-\d{2}$/, "Date must be in YYYY-MM-DD format"),
});

export type TagHistoryPayload = z.infer<typeof TagHistoryRequestSchema>;
