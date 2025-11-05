import { z } from "zod";

export const CaseRequestBodySchema = z.object({
  comments: z.string(),
  subject: z.string().min(1, "Please enter a subject"),
  path: z.string(),
  support_evidence: z.record(z.any()).nullish(),
});

export const CaseResponseBodySchema = z.object({
  comments: z.string(),
  subject: z.string(),
  path: z.string(),
  case_id: z.number(),
  user_id: z.number(),
});

export const CaseStatusSchema = z.union([
  z.literal("assigned"),
  z.literal("unassigned"),
  z.literal("closed"),
]);

export const CaseListItemResponseSchema = CaseResponseBodySchema.extend({
  status: CaseStatusSchema,
  create_dtm: z.string(),
  update_dtm: z.string().nullish(),
  resolved_dtm: z.string().nullish(),
  agent_comments: z.string().nullish(),
  agent_id: z.number().nullish(),
  root_cause_id: z.number().nullish(),
  support_evidence: z.record(z.any()).nullish(),
});

export const CaseListAgentItemResponseSchema = z.object({
  agent_comments: z.string().nullish(),
  agent_id: z.number().nullish(),
  case_id: z.number(),
  comments: z.string().nullish(),
  dc_theater: z.string().nullish(),
  create_dtm: z.string(),
  path: z.string().nullish(),
  resolved_dtm: z.string().nullish(),
  root_cause_id: z.number().nullish(),
  status: CaseStatusSchema,
  subject: z.string(),
  updated_dtm: z.string().nullish(),
  user_id: z.number(),
  support_evidence: z.record(z.any()).nullish(),
});

export const CaseListAgentFiltersSchema = z.object({
  assigned_user_id: z.number().nullish(),
  user_id: z.number().nullish(),
  status: CaseStatusSchema,
});

export type TCaseRequestBody = z.infer<typeof CaseRequestBodySchema>;
export type TCaseResponseBody = z.infer<typeof CaseResponseBodySchema>;
export type TCaseListItemResponse = z.infer<typeof CaseListItemResponseSchema>;
export type TCaseListAgentItemResponse = z.infer<
  typeof CaseListAgentItemResponseSchema
>;
export type TCaseListAgentFilters = z.infer<typeof CaseListAgentFiltersSchema>;

export const SprintGoalsResponseSchema = z.object({
  url: z.string().url(),
  expires_secs: z.number().positive(),
});

export type TSprintGoalsResponse = z.infer<typeof SprintGoalsResponseSchema>;
