import { z } from "zod";

export const SerialTaggingPayloadSchema = z.object({
  tag_ids: z.array(z.number()),
  serial_numbers: z.array(z.coerce.string()),
  engagement_id: z.number(),
  comment: z.string().optional(),
  config_strategy: z.string().nullable(),
});

const SerialTaggingResponseBase = z.object({
  request_id: z.coerce.number(),
  external_job_id: z.coerce.string().catch(""),
  message: z.string().catch(""),
});

const SerialTaggingResponseSucess = SerialTaggingResponseBase.extend({
  success: z.literal(true),
  external_run_id: z.coerce.string().catch(""),
});

const SerialTaggingResponseFailure = SerialTaggingResponseBase.extend({
  success: z.literal(false),
  external_run_id: z.coerce.string().nullable().catch(null),
});

export const SerialTaggingResponseSchema = z.discriminatedUnion("success", [
  SerialTaggingResponseSucess,
  SerialTaggingResponseFailure,
]);

export type TSerialTaggingPayloadOutput = z.infer<
  typeof SerialTaggingPayloadSchema
>;
export type TSerialTaggingPayloadInput = z.input<
  typeof SerialTaggingPayloadSchema
>;

export type TSerialTaggingResponseOutput = z.infer<
  typeof SerialTaggingResponseSchema
>;
export type TSerialTaggingResponseInput = z.input<
  typeof SerialTaggingResponseSchema
>;
