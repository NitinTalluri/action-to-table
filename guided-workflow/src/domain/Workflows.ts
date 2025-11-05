import { z } from "zod";

export const WorkflowUiEnum = z.enum([
  "log-signoff",
  "instance-tagging",
  "serial-tagging",
  "bulk-tagging",
  "snif-report",
  "generate-docusign-scope",
  "site-report",
  "acat-discovery",
  "host-name-relink",
  "host-name-site-moves",
  "tag-history",
  "add-to-contract",
  "customer-upload",
  "collector-upload",
  "canvas-actions",
  "general-notification",
  "sea-upload",
  "macd-upload",
  "macd-audit",
  "macd-historical-upload",
]);

export type TWorkflowUiEnum = z.infer<typeof WorkflowUiEnum>;

export const isWorkflowUiEnum = (str: string): str is TWorkflowUiEnum => {
  return WorkflowUiEnum.safeParse(str).success;
};

export const WorkflowTreeSchema = z.array(
  z.object({
    tree_id: z.number(),
    action_label: z.string(),
    ui_enum: z.string().nullable(),
    child_ids: z.array(z.number()),
  }),
);

export type TWorkflowTree = z.infer<typeof WorkflowTreeSchema>;

export const WorkflowNotificationCategoryEnum = z.enum([
  "result",
  "task",
  "error",
  "pending",
]);

export type TWorkflowNotificationCategoryEnum = z.infer<
  typeof WorkflowNotificationCategoryEnum
>;

export const WorkflowNotificationSummarySchema = z.object({
  notification_id: z.number(),
  tree_id: z.number(),
  notification_category: WorkflowNotificationCategoryEnum,
  subject: z.string().optional(),
  dc_user_id: z.number(),
  dc_engagement_id: z.number().nullable(),
  request_id: z.number().nullable(),
  canvas_id: z.number().nullable(),
  workflow_enum: z.string().nullable(),
  external_job_id: z.string().nullable(),
  external_run_id: z.string().nullable(),
  create_dtm: z.string(),
  update_dtm: z.string().nullable(),
  created_by: z.string().optional(),
});

export type TSummaryNotification = z.infer<
  typeof WorkflowNotificationSummarySchema
>;

export const WorkflowNotificationDetailSchema =
  WorkflowNotificationSummarySchema.extend({
    data: z.array(z.unknown()).nullable(),
  });

export type TDetailNotification = z.infer<
  typeof WorkflowNotificationDetailSchema
>;

export const PresignedUrlResponseSchema = z.object({
  url: z.string(),
  requested_url: z.string(),
  expires_secs: z.number(),
});

const LogSignOffRequestSchema = z.object({
  is_deferred: z.literal(false),
  signoff_method: z.string(),
  signoff_event: z.string(),
  sign_off_identity: z.string(),
  booking_contract: z.number(),
  effective_date: z.string(),
  dc_engagement_id: z.number().int(),
  dc_user_id: z.number().int(),
  notes: z.string().optional(),
});

export type TLogSignOffRequestSchema = z.infer<typeof LogSignOffRequestSchema>;

export const GenericJobResponseSchema = z.object({
  request_id: z.number(),
  notification_id: z.number(),
  message: z.string(),
  success: z.literal(true),
});

export type TGenericJobResponse = z.infer<typeof GenericJobResponseSchema>;
