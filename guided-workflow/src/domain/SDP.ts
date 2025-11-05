import { z } from "zod";

// API Schemas
export const SdpApiSchema = z.array(
  z.object({
    deliverable_desc: z.string(),
    deliverable_id: z.number(),
    sub_task_id: z.number(),
    subtask_desc: z.string(),
    task_desc: z.string(),
    task_id: z.number(),
    subtask_frequency: z.number().nullable(),
    subtask_hours: z.number().nullable(),
    task_frequency: z.number().nullable(),
    task_hours: z.number().nullable(),
  }),
);

export const SubtaskApiSchema = z.object({
  sub_task_id: z.number(),
  subtask_desc: z.string(),
  subtask_doc_link: z.string().nullable(),
  subtask_desc_long: z.string().nullable(),
  task_ids: z.array(z.number()),
  buying_program_type_ids: z.array(z.number()),
  pricing_type_ids: z.array(z.number()),
  sold_as_service_type_ids: z.array(z.number()),
  frequency: z.number().nullish(),
  hours: z.number().nullish(),
  cycle_days: z.number().nullish(),
});

export const TaskApiSchema = z.object({
  task_id: z.number(),
  task_desc: z.string(),
  task_doc_link: z.string().nullable(),
  task_desc_long: z.string().nullable(),
  sub_task_ids: z.array(z.number()),
  deliverable_ids: z.array(z.number()),
  frequency: z.number().nullish(),
  hours: z.number().nullish(),
  anchor_date_id: z.number().nullable(),
  cycle_iterator_id: z.number().nullable(),
  due_date_offset: z.number().nullish(),
});

export const DeliverableApiSchema = z.object({
  deliverable_id: z.number(),
  deliverable_desc: z.string(),
  deliverable_doc_link: z.string().nullable(),
  task_ids: z.array(z.number()),
});

export const LifecycleApiSchema = z.object({
  lifecycle_id: z.number(),
  lifecycle_desc: z.string(),
  lifecycle_doc_link: z.string().nullable(),
  deliverable_ids: z.array(z.number()),
});

export const EnablementOptionApiSchema = z.object({
  id: z.number(),
  value: z.string(),
  isDeleted: z.boolean(),
  isSelected: z.boolean(),
});

// Form Schemas
export const SubtaskFormSchema = z.object({
  sub_task_id: z.number().optional(),
  subtask_desc: z.string().min(1, "SubTask Name is required."),
  subtask_doc_link: z.string().optional(),
  subtask_desc_long: z.string().optional(),
  task_ids: z.array(z.number()).optional(),
  buying_program_type_ids: z
    .array(z.number())
    .min(1, "At least one buying program must be selected."),
  pricing_type_ids: z
    .array(z.number())
    .min(1, "At least one pricing model must be selected."),
  sold_as_service_type_ids: z
    .array(z.number())
    .min(1, "At least one service type must be selected."),
  frequency: z.coerce.number().nullish(),
  hours: z.coerce.number().nullish(),
  cycle_days: z.coerce
    .number()
    .gte(-365, "Cycle Days cannot be less than -365 days")
    .lte(365, "Cycle Days cannot be greater than 365 days"),
});

export const TaskFormSchema = z.object({
  task_id: z.number().optional(),
  task_desc: z.string().min(1, "Task Name is required."),
  task_doc_link: z.string().optional(),
  task_desc_long: z.string().optional(),
  sub_task_ids: z.array(z.number()).optional(),
  deliverable_ids: z.array(z.number()).optional(),
  frequency: z.coerce.number().nullish(),
  hours: z.coerce.number().nullish(),
  anchor_date_id: z.coerce.number(),
  cycle_iterator_id: z.coerce.number(),
  due_date_offset: z.coerce
    .number()
    .gte(-365, "Due Days Offset cannot be less than -365 days")
    .lte(365, "Due Days Offset cannot be greater than 365 days"),
});

export const DeliverableFormSchema = z.object({
  deliverable_id: z.number().optional(),
  deliverable_desc: z.string().min(1, "Description is required."),
  deliverable_doc_link: z.string().optional(),
  task_ids: z.array(z.number()).optional(),
});

export const LifecycleFormSchema = z.object({
  lifecycle_id: z.number().optional(),
  lifecycle_desc: z.string().min(1, "Description is required."),
  lifecycle_doc_link: z.string().optional(),
  deliverable_ids: z.array(z.number()).optional(),
});

export const EnablementOptionFormSchema = z.object({
  id: z.number(),
  value: z.string(),
  isDeleted: z.boolean(),
  isSelected: z.boolean(),
});

// Type Definitions
export type TSdpData = z.infer<typeof SdpApiSchema>;
export type TSubtask = z.infer<typeof SubtaskApiSchema>;
export type TTask = z.infer<typeof TaskApiSchema>;
export type TDeliverable = z.infer<typeof DeliverableApiSchema>;
export type TLifecycle = z.infer<typeof LifecycleApiSchema>;
export type TEnablementOption = z.infer<typeof EnablementOptionApiSchema>;

export type TSubtaskForm = z.infer<typeof SubtaskFormSchema>;
export type TTaskForm = z.infer<typeof TaskFormSchema>;
export type TDeliverableForm = z.infer<typeof DeliverableFormSchema>;
export type TLifecycleForm = z.infer<typeof LifecycleFormSchema>;
export type TEnablementOptionForm = z.infer<typeof EnablementOptionFormSchema>;
export type TTableRow = z.infer<typeof SdpApiSchema>[number];
