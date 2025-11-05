import { z } from "zod";

// Summary View Deliverables
export const DeliverableItem = z.object({
  task_id: z.number(),
  subtask_desc: z.string(),
  task_desc: z.string().nullable(),
  sub_task_id: z.number(),
  deliverable_id: z.number(),
  deliverable_desc: z.string().nullable(),
  time_cycle: z.string(),
  cycle_days: z.number(),
  due_date_offset: z.number(),
  anchor_date: z.string(),
  anchor_date_id: z.number(),
  engagement_name: z.string().nullable(),
  dc_engagement_id: z.number(),
  booking_contract: z.number(),
  buying_program_name: z.string().nullable(),
  buying_program_type_id: z.number(),
  sold_as_service_name: z.string().nullable(),
  sold_as_service_type_id: z.number(),
  pricing_model_name: z.string().nullable(),
  pricing_model_type_id: z.number(),
});

export const DeliverablesResponseSchema = z.array(DeliverableItem).default([]);

export type TDeliverables = z.infer<typeof DeliverableItem>;

export type TDeliverablesResponse = z.infer<typeof DeliverablesResponseSchema>;

// Detail View Deliverables
export const ScheduledDeliverableTaskItem = z.object({
  booking_contract: z.number(),
  cisco_cco_id: z.string(),
  dc_engagement_id: z.number(),
  deliverable_desc: z.string(),
  deliverable_id: z.number(),
  due_date: z.string(),
  engagement_name: z.string(),
  sort_date: z.string(),
  subtask_desc: z.string(),
  sub_task_id: z.number(),
  task_desc: z.string(),
  task_id: z.number(),
});

export const ScheduledDeliverableItem = z.object({
  header_name: z.string(),
  booking_contract: z.number(),
  task_desc: z.string(),
  due_date: z.string(),
  cycle: z.number(),
  deliverable_id: z.number(),
  tasks: z.array(ScheduledDeliverableTaskItem).default([]),
});

export const ScheduledDeliverablesResponseSchema = z
  .array(ScheduledDeliverableItem)
  .default([]);

export type TScheduledDeliverableTaskItem = z.infer<
  typeof ScheduledDeliverableTaskItem
>;
export type TScheduledDeliverableItem = z.infer<
  typeof ScheduledDeliverableItem
>;
export type TScheduledDeliverablesResponse = z.infer<
  typeof ScheduledDeliverablesResponseSchema
>;

// Active View Deliverables
export const ActiveDeliverableTaskItem = z.object({
  booking_contract: z.number(),
  completed_by: z.string().nullable(),
  closed_date: z.string().nullable(),
  completion_type_id: z.number().nullable(),
  cycle: z.number(),
  dc_engagement_id: z.number(),
  deliverable_desc: z.string().nullable(),
  deliverable_id: z.number(),
  due_date: z.string(),
  engagement_name: z.string().nullable(),
  header_name: z.string(),
  is_closed: z.boolean(),
  sort_date: z.string().nullable(),
  subtask_desc: z.string(),
  sub_task_id: z.number(),
  task_desc: z.string(),
  task_id: z.number(),
  task_status: z.string(),
});

export const ActiveDeliverableItem = z.object({
  header_name: z.string(),
  booking_contract: z.number(),
  task_desc: z.string(),
  due_date: z.string(),
  cycle: z.number(),
  deliverable_id: z.number(),
  tasks: z.array(ActiveDeliverableTaskItem).default([]),
});

export const ActiveDeliverablesResponseSchema = z
  .array(ActiveDeliverableItem)
  .default([]);

export type TActiveDeliverableTaskItem = z.infer<
  typeof ActiveDeliverableTaskItem
>;
export type TActiveDeliverablesItem = z.infer<typeof ActiveDeliverableItem>;
export type TActiveDeliverablesResponse = z.infer<
  typeof ActiveDeliverablesResponseSchema
>;

// Closed View Deliverables
export const ClosedDeliverableTaskItem = z.object({
  booking_contract: z.number(),
  closed_date: z.string(),
  completed_by: z.string(),
  completion_type_id: z.number(),
  cycle: z.number(),
  dc_engagement_id: z.number(),
  deliverable_desc: z.string(),
  deliverable_id: z.number(),
  due_date: z.string(),
  engagement_name: z.string(),
  header_name: z.string(),
  is_closed: z.boolean(),
  sort_date: z.string(),
  sub_task_id: z.number(),
  subtask_desc: z.string(),
  task_desc: z.string(),
  task_id: z.number(),
  task_status: z.string(),
});

export const ClosedDeliverableItem = z.object({
  header_name: z.string(),
  booking_contract: z.number(),
  task_desc: z.string(),
  due_date: z.string(),
  cycle: z.number(),
  deliverable_id: z.number(),
  tasks: z.array(ClosedDeliverableTaskItem).default([]),
});

export const ClosedDeliverablesResponseSchema = z
  .array(ClosedDeliverableItem)
  .default([]);

export type TClosedDeliverableTaskItem = z.infer<
  typeof ClosedDeliverableTaskItem
>;
export type TClosedDeliverableItem = z.infer<typeof ClosedDeliverableItem>;
export type TClosedDeliverablesResponse = z.infer<
  typeof ClosedDeliverablesResponseSchema
>;

export const UpdateTaskStatusSchema = z.object({
  sub_task_id: z.number(),
  booking_contract: z.number(),
  cycle_iterator: z.number(),
  completion_type_id: z.number(),
  dc_engagement_id: z.number(),
  due_date: z.string(),
  is_completed: z.boolean(),
  note: z.string(),
});

export const UpdateTaskStatusResponseSchema = z.object({
  sub_task_id: z.number(),
  booking_contract: z.number(),
  dc_user_id: z.number(),
  cycle_iterator: z.number(),
  completion_type_id: z.number(),
  dc_engagement_id: z.number(),
  due_date: z.string(),
  created_by: z.string(),
  create_dtm: z.string(),
  updated_by: z.string().nullable(),
  update_dtm: z.string().nullable(),
  is_completed: z.boolean(),
});

export type TUpdateTaskStatus = z.infer<typeof UpdateTaskStatusSchema>;
export type TUpdateTaskStatusResponse = z.infer<
  typeof UpdateTaskStatusResponseSchema
>;
