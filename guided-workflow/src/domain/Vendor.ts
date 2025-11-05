import z from "zod";

import { IUserAssignment } from "~/domain/ManagerPortal";

export const VendorAttachCAMReviewSchema = z.object({
  isSubmitting: z.boolean(),
});

export const AssignmentSchema = z.object({
  booking_contract: z.number(),
  dc_user_id: z.number(),
  dc_engagement_id: z.number(),
  display_name: z.string(),
  service_role_id: z.number(),
  sub_allocation_hw: z.number(),
});

export const VendorPortalDeliverableItemSchema = z.object({
  booking_contract: z.number(),
  deliverable_id: z.number(),
  deliverable_desc: z.string(),
  task_id: z.number(),
  task_desc: z.string(),
  sub_task_id: z.number(),
  subtask_desc: z.string(),
  task_anchor_date_id: z.number(),
  task_cycle_iterator_name: z.string(),
  task_anchor_date_name: z.string(),
  task_cycle_iterator_id: z.number(),
  due_date_offset: z.number(),
  cycle_days: z.number(),
  sdp_assigned_user_ids: z.array(z.number()),
});

export const VendorPortalDeliverableListSchema = z.array(
  VendorPortalDeliverableItemSchema,
);

export const SelectedSubtaskIdsSchema = z.array(z.number());

export type TVendorPortalDeliverableList = z.infer<
  typeof VendorPortalDeliverableListSchema
>;

export type TVendorAttachCAMReview = z.infer<
  typeof VendorAttachCAMReviewSchema
>;

export type TAssignment = z.infer<typeof AssignmentSchema>;

export type TSelectedSubtasks = z.infer<typeof SelectedSubtaskIdsSchema>;

export type TCAMVendorAssignment = {
  booking_contract: number;
  assignments: IUserAssignment[];
  sub_task_ids: TSelectedSubtasks;
};
