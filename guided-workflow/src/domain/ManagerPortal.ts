import { z } from "zod";

import { truthyEnum } from "./Contracts";

export const ManagerPortalEngagementResponseSchema = z.object({
  created_by: z.string().nullable(),
  create_dtm: z.string().nullable(),
  update_dtm: z.string().nullable(),
  updated_by: z.string().nullable(),
  is_deleted: truthyEnum,
  dc_engagement_id: z.number().nullable(),
  engagement_name: z.string().nullable(),
  is_sfc: truthyEnum,
  is_cxea: truthyEnum,
  is_software: truthyEnum,
  sfc_agreement_type: z.number().nullable(),
  notes: z.string().nullable(),
});

export type TManagerPortalEngagementResponse = z.infer<
  typeof ManagerPortalEngagementResponseSchema
>;

export const BookingUserAssignmentSchema = z.object({
  display_name: z.string(),
  booking_contract: z.number(),
  dc_user_id: z.number().min(0),
  service_role_id: z.number().min(0),
  sub_allocation_sw: z.coerce.number().min(0).max(1),
  sub_allocation_hw: z.coerce.number().min(0).max(1),
  dc_engagement_id: z.number(),
});

const SortedBookingUserAssignmentSchema = z
  .array(BookingUserAssignmentSchema)
  .transform((data) => {
    return data.sort((a, b) => a.dc_user_id - b.dc_user_id);
  });

/**
 * Schema for claiming a booking in the Manager Portal
 * @property booking_override_reason_id - Optional identifier for booking override claim reasons
 */
export const ManagerPortalClaimBookingSchema = z.object({
  booking_contract: z.number(),
  renewed_from: z.array(z.number()),
  dc_engagement_id_default: z.number(),
  booking_override_reason_id: z.number().nullable(),
});

export const ManagerPortalUnclaimedBookingSchema = z.object({
  booking_contract: z.number(),
  account_name: z.string(),
  booked_sav_1: z.string().nullable(),
  booked_sav_2: z.string().nullable(),
  booked_sav_3: z.string().nullable(),
  booked_theater_id: z.number(),
  is_virtual: z.boolean(), // A virtual booking is a booking that has a negative value for booking_contract
  booked_usd: z.number(),
  agreement_start_date: z.string().date(),
  agreement_end_date: z.string().date(),
  effective_end_date: z.string().date(),
  sold_as_service_type_id: z.number(),
  sold_as_pricing_type_id: z.number(),
  buying_program_type_id: z.number(),
  booking_country: z.string().nullable(),
  cam_revenue_usd: z.number().nullable(),
  cam_cost_usd: z.number().nullable(),
  booked_date: z.string().date().nullable(),
  booked_sw: z.number(),
  booked_hw: z.number(),
  calculated_sw: z.number().nullish(),
  calculated_hw: z.number().nullish(),
  sourced_allocation: z.number().nullable(),
  quote_for_audit: z.string().nullable(),
  derived_new_renew: z.string().nullable(),
  renewed_from: z.array(z.number()).nullable(),
  is_cxea: z.boolean().nullable(), // CXEA Scale booking indicator
  dc_engagement_id_default: z.number().nullish(),
});

export const ManagerPortalClaimedBookingSchema =
  ManagerPortalUnclaimedBookingSchema.extend({
    is_cxea: z.boolean(),
    assignments: SortedBookingUserAssignmentSchema,
    allocation_fte_total: z.coerce.number(),
    allocation_fte_sw_ratio: z.coerce.number(),
    allocation_fte_hw_ratio: z.coerce.number(),
    is_current_and_unassigned: z.boolean(),
    is_disengaged: z.boolean(),
    claimed_and_managed_by: z.number(),
    extended_count: z.number(),
    effective_end_date: z.string().date().nullable(),
    delivery_status: z.string(),
    sales_level_id: z.number().nullish(),
    node_level1: z.string().nullish(),
    node_level2: z.string().nullish(),
    node_level3: z.string().nullish(),
    node_level4: z.string().nullish(),
    node_segment: z.string().nullish(),
  });

export const ModifyClaimedBookingSchema = z.object({
  booking_contract: z.number().min(0),
  dc_engagement_id_default: z.number().min(0),
});

export const ModifyClaimedBookingCalculatedSchema = z.object({
  booking_contract: z.number().min(0),
  calculated_sw: z.number().min(0),
  calculated_hw: z.number().min(0),
});

export const ModifyBookingUserAssignmentSchema = z.object({
  booking_contract: z.number().min(0),
  assignments: z.array(BookingUserAssignmentSchema),
});

export const ModifyBookingDcTypesSchema = z.object({
  booking_contract: z.number().min(1),
  sold_as_service_type_id: z.number().min(1),
  sold_as_pricing_type_id: z.number().min(1),
  buying_program_type_id: z.number().min(1),
});

export const ModifyBookingCurrentSalesLevelSchema = z.object({
  booking_contract: z.number().min(0),
  sales_level_id: z.number().min(0),
});

export const RenewableBookingsSchema = z.object({
  booking_contract: z.number(),
  account_name: z.string(),
  agreement_start_date: z.string().date(),
  agreement_end_date: z.string().date(),
  effective_end_date: z.string().date(),
  renewed_from: z.array(z.number()).nullable(),
  engagements: z
    .array(
      z.object({
        engagement_name: z.string(),
        dc_engagement_id: z.number(),
      }),
    )
    .nullable(),
  buying_program_type_id: z.number(),
  sold_as_service_type_id: z.number(),
  sold_as_pricing_type_id: z.number(),
  manager_name: z.string().nullable(),
  employee_names: z.string().array().nullable(),
});

export const DisengagementSchema = z.object({
  disengagement_reason_id: z.number(),
  booking_contract: z.number(),
  notes: z.string().nullish(),
});

export const AttachedEngagementSchema = z.object({
  booking_contract: z.number().min(1),
  dc_engagement_id: z.number().min(1),
});

export const DisengagementResponseSchema = DisengagementSchema.extend({
  dc_user_id: z.number().nullable(),
});

export const ReplaceUserSchema = z.object({
  prev_user_id: z.number().min(0),
  new_user_id: z.number().min(0),
  booking_contract: z.number().min(0),
});

export const AllocationRequestSchema = z.object({
  allocation_fte_hw_ratio: z.number(),
  allocation_fte_sw_ratio: z.number(),
  booking_contract: z.number(),
});

export const CreateBookingRequestSchema = z.object({
  account_name: z.string().min(1, "Name is required"),
  buying_program_type_id: z.coerce
    .number()
    .min(1, "Buying Program is required"),
  sold_as_pricing_type_id: z.coerce
    .number()
    .min(1, "Pricing Model is required"),
  booked_theater_id: z.coerce.number().min(1, "Theater is required"),
  sold_as_service_type_id: z.coerce.number().min(1, "Service Type is required"),
  agreement_start_date: z.string().date(),
  agreement_end_date: z.string().date(),
  allocation_fte_hw_ratio: z
    .number()
    .min(0, "Allocation ratio must be positive"),
  allocation_fte_sw_ratio: z
    .number()
    .min(0, "Allocation ratio must be positive"),
  booking_country: z.string().nullish(),
  cam_revenue_usd: z.coerce.number(),
  sourced_allocation: z.coerce.number().nullish(),
  quote_for_audit: z.literal("manager_portal").nullish(),
  booked_usd: z.number().nullish(),
  cam_cost_usd: z.coerce.number(),
  booked_date: z.string().nullish(),
  sold_as_sw_allocation: z.number().nullish(),
  sold_as_hw_allocation: z.number().nullish(),
  ib_calc_sw_allocation: z.number().nullish(),
  ib_calc_hw_allocation: z.number().nullish(),
  booking_contract_type_id: z.coerce.number().nullish(),
});

export const ManagerPortalContractScopeSchema = z.enum(["all", "direct"]);

export type IVerifiedBookingModifyDcTypes = z.infer<
  typeof ModifyBookingDcTypesSchema
>;

export type IModifyBookingUserAssignment = z.infer<
  typeof ModifyBookingUserAssignmentSchema
>;

export type TManagerPortalUnclaimedBooking = z.infer<
  typeof ManagerPortalUnclaimedBookingSchema
>;

export type TManagerPortalClaimedBooking = z.infer<
  typeof ManagerPortalClaimedBookingSchema
>;

export type IClaimedBookingModify = z.infer<typeof ModifyClaimedBookingSchema>;

export type IClaimedBookingModifyCalculated = z.infer<
  typeof ModifyClaimedBookingCalculatedSchema
>;

export type IUserAssignment = z.infer<typeof BookingUserAssignmentSchema>;

export type TManagerPortalContractScope = z.infer<
  typeof ManagerPortalContractScopeSchema
>;

export type TManagerPortalClaimBooking = z.infer<
  typeof ManagerPortalClaimBookingSchema
>;

export type TRenewableBookings = z.infer<typeof RenewableBookingsSchema>;

export type TDisengagement = z.infer<typeof DisengagementSchema>;

export type TAttachedEngagement = z.infer<typeof AttachedEngagementSchema>;

export type TDisengagementResponse = z.infer<
  typeof DisengagementResponseSchema
>;

export type IReplaceUser = z.infer<typeof ReplaceUserSchema>;

export type TAllocationRequest = z.infer<typeof AllocationRequestSchema>;

export type TCreateBookingRequest = z.infer<typeof CreateBookingRequestSchema>;

export type TModifyBookingCurrentSalesLevel = z.infer<
  typeof ModifyBookingCurrentSalesLevelSchema
>;
