import { z } from "zod";

export const NotificationTypeEnums = z.enum([
  "text",
  "download",
  "table",
  "parameters",
  "code",
]);

export const EngagementLinkTypeEnums = z.enum([
  "acat_links",
  "mce_links",
  "party_links",
  "smart_links",
]);

export const TextNotificationDataSchema = z.object({
  type: z.literal(NotificationTypeEnums.Enum.text),
  data: z.string(),
  timestamp: z.string().nullish(),
});

export const DownloadNotificationDataSchema = z.object({
  type: z.literal(NotificationTypeEnums.Enum.download),
  data: z.object({
    label: z.string(),
    url: z.string(),
  }),
});

export const TableNotificationDataSchema = z.object({
  type: z.literal(NotificationTypeEnums.Enum.table),
  data: z.record(z.unknown()),
});

export const EngagementLinkSchema = z.object({
  dc_engagement_id: z.number(),
  id: z.number(),
  last_updated: z.string().nullable(),
  link_type: EngagementLinkTypeEnums,
});

export const DefaultParametersNotificationDataSchema = z.object({
  type: z.literal(NotificationTypeEnums.Enum.parameters),
  data: z.record(z.string(), z.unknown()),
  form_data: z.record(z.unknown()),
  timestamp: z.string().optional(),
});

export const CanvasParametersNotificationDataSchema = z.object({
  type: z.literal(NotificationTypeEnums.Enum.parameters),
  data: z.record(z.string(), z.unknown()),
  form_data: z.object({
    canvas_desc: z.string(),
    canvas_name: z.string(),
    canvas_type: z.string(),
    canvas_id: z.number(),
    collector_request_ids: z.array(z.number()).catch([]),
    customer_request_ids: z.array(z.number()).catch([]),
    historical_snapshot_name: z.string().nullish(),
    dc_engagement_id: z.number(),
    files: z.array(
      z.object({
        name: z.string(),
      }),
    ),
    tag_ids: z.array(z.number()).catch([]),
    _engagement_links: z
      .record(EngagementLinkTypeEnums, z.array(EngagementLinkSchema))
      .nullish(),
  }),
  timestamp: z.string().nullish(),
});

export const ParametersNotificationDataSchema = z.union([
  DefaultParametersNotificationDataSchema,
  CanvasParametersNotificationDataSchema,
]);

export type ICanvasParameterNotification = z.infer<
  typeof CanvasParametersNotificationDataSchema
>;

export type IParameterNotification = z.infer<
  typeof ParametersNotificationDataSchema
>;

export const CodeNotificationDataSchema = z.object({
  type: z.literal(NotificationTypeEnums.Enum.code),
  data: z.union([z.string(), z.record(z.unknown())]),
});

export const NotificationDataSchema = z.union([
  TextNotificationDataSchema,
  DownloadNotificationDataSchema,
  TableNotificationDataSchema,
  ParametersNotificationDataSchema,
  CodeNotificationDataSchema,
]);
