import { z } from "zod";

import {
  InstanceIdGridSchema,
  TInstanceId,
} from "~/domain/grids/InstanceIdGrid";

import {
  SerialNumberGridSchema,
  TSerialNumberGrid,
} from "./grids/SerialNumberGrid";

export const InstanceIdApiConvertSchema = InstanceIdGridSchema.transform<
  TInstanceId["instance_id"]
>((val) => {
  return val.instance_id;
});
export type TInstanceIdApi = z.infer<typeof InstanceIdApiConvertSchema>;
export const InstanceIdApiConvertArraySchema = z.array(
  InstanceIdApiConvertSchema,
);
const InstanceIdApiArraySchema = z.array(z.number());

/*
  Serial Numbers
 */

const SerialNumberApiConvertSchema = SerialNumberGridSchema.transform<
  TSerialNumberGrid["serial_number"]
>((val) => {
  return val.serial_number;
});
export type TSerialNumberApi = z.infer<typeof SerialNumberApiConvertSchema>;
const SerialNumberApiConvertArraySchema = z.array(SerialNumberApiConvertSchema);
const SerialNumberApiArraySchema = z.array(z.string());

export const IdsApiConvertSchema = z.discriminatedUnion("id_type", [
  z.object({
    id_type: z.literal("instance_id"),
    ids: InstanceIdApiConvertArraySchema,
  }),
  z.object({
    id_type: z.literal("serial_number"),
    ids: SerialNumberApiConvertArraySchema,
  }),
]);

export const IdTypeSchema = z.enum(["instance_id", "serial_number"]);
export type TIdType = z.infer<typeof IdTypeSchema>;

const SnifReportInstanceIdPayloadSchema = z.object({
  ids: InstanceIdApiArraySchema,
  engagement_id: z.coerce.number(),
  id_type: z.literal(IdTypeSchema.Enum["instance_id"]),
});

const SnifReportSerialNumberPayloadSchema = z.object({
  ids: SerialNumberApiArraySchema,
  engagement_id: z.coerce.number(),
  id_type: z.literal(IdTypeSchema.Enum["serial_number"]),
});

export const SnifReportPayloadSchema = z.discriminatedUnion("id_type", [
  SnifReportInstanceIdPayloadSchema,
  SnifReportSerialNumberPayloadSchema,
]);

const SnifReportResponseBase = z.object({
  request_id: z.coerce.number(),
  external_job_id: z.coerce.string().catch(""),
  message: z.string().catch(""),
});

const SnifReportResponseSuccess = SnifReportResponseBase.extend({
  success: z.literal(true),
  external_run_id: z.coerce.string().catch(""),
});

export type TSnifReportResponseSuccess = z.infer<
  typeof SnifReportResponseSuccess
>;

const SnifReportResponseFailure = SnifReportResponseBase.extend({
  success: z.literal(false),
  external_run_id: z.coerce.string().nullable().catch(null),
});

export const SnifReportResponseSchema = z.discriminatedUnion("success", [
  SnifReportResponseSuccess,
  SnifReportResponseFailure,
]);

export type TSnifReportResponseOutput = z.infer<
  typeof SnifReportResponseSchema
>;
export type TSnifReportResponseInput = z.input<typeof SnifReportResponseSchema>;
export type TSnifReportPayload = z.infer<typeof SnifReportPayloadSchema>;
