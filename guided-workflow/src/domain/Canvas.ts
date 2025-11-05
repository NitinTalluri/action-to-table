import { z } from "zod";

import { UnifiedCanvasFileSchema } from "./CanvasFiles";
import { PinboardSchema } from "./Pinboard";

const canvasStatusEnum = z.enum(["running", "success", "failed"]);
const canvasTypeEnum = z.enum([
  "current view canvas",
  "sourced file canvas",
  "unified view canvas",
]);

export type TCanvasType = z.infer<typeof canvasTypeEnum>;
export type TCanvasStatus = z.infer<typeof canvasStatusEnum>;

const canvasId = z.number();
const canvasName = z.string();
const canvasDesc = z.string().catch("");
const dcEngagementId = z.number();
const canvasType = canvasTypeEnum.catch(
  canvasTypeEnum.enum["unified view canvas"],
);
const canvasStatus = canvasStatusEnum.catch(canvasStatusEnum.enum.success);
const createDtm = z.string();
const pinboards = z.array(PinboardSchema).catch([]);
const extractActions = z.number().catch(0);
const tagActions = z.number().catch(0);

export const CanvasItem = z.object({
  canvas_id: canvasId,
  canvas_name: canvasName,
  canvas_desc: canvasDesc,
  dc_engagement_id: dcEngagementId,
  canvas_status: canvasStatus,
  canvas_type: canvasType,
  create_dtm: createDtm,
  pinboards: pinboards,
  extract_actions: extractActions,
  tag_actions: tagActions,
  notification_id: z.number().nullable(),
  enabled: z.boolean().default(true),
});
export const CanvasPartialItem = z
  .object({
    canvas_id: canvasId,
    canvas_name: canvasName,
    canvas_desc: canvasDesc,
    dc_engagement_id: dcEngagementId,
    canvas_status: canvasStatus,
    canvas_type: canvasType,
    create_dtm: createDtm,
    notification_id: z.number().nullable(),
  })
  .describe(
    "API responds with partial canvas data when creating a new canvas, editing or deleting a canvas",
  );

export type ICanvasItemResponse = z.input<typeof CanvasItem>;
export type ICanvas = z.infer<typeof CanvasItem>;
export type ICanvasPartial = z.infer<typeof CanvasPartialItem>;
export type ICanvasPartialResponse = z.input<typeof CanvasPartialItem>;

export const CanvasResponseSchema = z.array(CanvasItem);

const CanvasCreateBaseSchema = z.object({
  canvas_name: canvasName,
  canvas_desc: canvasDesc,
  dc_engagement_id: dcEngagementId,
});

export const CanvasCreateUnifiedViewSchema = CanvasCreateBaseSchema.extend({
  canvas_type: z.literal("unified view canvas"),
  files: z.array(UnifiedCanvasFileSchema),
  tag_ids: z.array(z.number()),
  customer_request_ids: z.array(z.number()),
  collector_request_ids: z.array(z.number()),
  historical_snapshot_name: z.string().nullable(),
});

export const CanvasRefreshUnifiedViewSchema =
  CanvasCreateUnifiedViewSchema.extend({
    canvas_id: canvasId,
  });

const CreateCanvasSchema = CanvasCreateUnifiedViewSchema;

const RefreshCanvasSchema = CanvasRefreshUnifiedViewSchema;

export type TCanvasCreateUnifiedView = z.infer<
  typeof CanvasCreateUnifiedViewSchema
>;

export type TCanvasRefreshUnifiedView = z.infer<
  typeof CanvasRefreshUnifiedViewSchema
>;

export type TCreateCanvasParams = z.infer<typeof CreateCanvasSchema>;

export type TRefreshCanvasParams = z.infer<typeof RefreshCanvasSchema>;

export const CustomerCollectorFileSchema = z.object({
  request_id: z.number(),
  effective_date: z.string(),
  source: z.string(),
  note: z.string(),
  file_name_id: z.number(),
  dc_engagement_id: z.number(),
  type: z.enum(["collector", "customer"]),
  file_name: z.string(),
});

export type TCustomerCollectorFile = z.infer<
  typeof CustomerCollectorFileSchema
>;

export const DeletedCanvasSchema = z.object({
  canvas_desc: z.string().nullish(),
  canvas_id: z.number(),
  canvas_name: z.string(),
  dc_engagement_id: z.number(),
  update_dtm: z.string().nullable(),
  updated_by: z.string().nullable(),
});

export type TDeletedCanvas = z.infer<typeof DeletedCanvasSchema>;

export const SnapshotDatesSchema = z.object({
  name: z.string(),
  snapshot_date: z.string(),
});

export type TSnapshotDates = z.infer<typeof SnapshotDatesSchema>;
