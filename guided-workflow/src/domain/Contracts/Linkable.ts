import { z } from "zod";

import { truthyEnum } from "./Truthy";

const LinkedContractsSchemaBase = z.object({
  account_name: z.string(),
  booking_contract: z.number(),
  bookings_role: z.string(),
  pricing_model: z.string().default("NONE"),
  service_name: z.string().default("UNKNOWN"),
  user_id: z.number(),
  dc_engagement_id: z.number().nullable(),
  engagement_name: z.string().nullable(),
  buying_program_name: z.string().nullable(),
});

export const LinkedContractResponseSchema = z.object({
  update_dtm: z.string().nullable(),
  created_by: z.string(),
  booking_contract: z.number(),
  dc_engagement_id: z.number(),
  create_dtm: z.string(),
  updated_by: z.string().nullable(),
  is_deleted: truthyEnum,
  dc_user_id: z.number(),
});

const LinkedContractsSchemaLinked = LinkedContractsSchemaBase.extend({
  dc_engagement_id: z.null(),
  engagement_name: z.null(),
  is_linkable: z.literal("T"),
});

const LinkedContractsSchemaUnlinked = LinkedContractsSchemaBase.extend({
  dc_engagement_id: z.number(),
  engagement_name: z.string().catch(""),
  is_linkable: z.literal("F"),
});

export const LinkableContractsSchema = z.discriminatedUnion("is_linkable", [
  LinkedContractsSchemaLinked,
  LinkedContractsSchemaUnlinked,
]);

export const LinkableContractsResponseSchema = z.array(LinkableContractsSchema);
export type ILinkableContracts = z.infer<typeof LinkableContractsSchema>;
export const parseLinkableContracts = (
  data: unknown,
): Promise<ILinkableContracts[]> => {
  return LinkableContractsResponseSchema.parseAsync(data);
};
