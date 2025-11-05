import { z } from "zod";

import { truthyEnum } from "./Truthy";

const ManagedContractSchema = z.object({
  allowed_service_levels: z.string().catch(""),
  contract_name: z.string().catch(""),
  contract_number: z.coerce.number(),
  notes: z.string().catch(""),
});

export const ManagedContractPostSchema = ManagedContractSchema.extend({
  user: z.string().describe("Email address"),
});

export const CreateMonitorContractResponseSchema = z.object({
  create_dtm: z.string(),
  is_deleted: truthyEnum,
  updated_by: z.string().nullable(),
  monitor_type_id: z.number(),
  monitor_notes: z.string().nullable(),
  update_dtm: z.string().nullable(),
  created_by: z.string(),
  contract_number: z.number(),
  dc_engagement_id: z.number(),
});

export default ManagedContractSchema;

export type ManagedContract = z.infer<typeof ManagedContractSchema>;

export type ManagedContractPost = z.infer<typeof ManagedContractPostSchema>;
