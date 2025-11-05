import { z } from "zod";

export const BookingUserAssignmentSchema = z.object({
  booking_contract: z.number().min(0),
  dc_user_id: z.number().min(0),
  service_role_id: z.number().min(0),
  sub_allocation_sw: z.number().min(0).max(1),
  sub_allocation_hw: z.number().min(0).max(1),
});

const SortedBookingUserAssignmentSchema = z
  .array(BookingUserAssignmentSchema)
  .transform((data) => {
    return data.sort((a, b) => a.dc_user_id - b.dc_user_id);
  });

const truthyEnum = z.enum(["T", "F"] as const);
const truthyBool = z
  .boolean()
  .or(truthyEnum)
  .transform<boolean>((v) => {
    if (typeof v === "boolean") {
      return v;
    }
    return v === "T";
  })
  .catch(false);

export const VerifiedBookingResponseSchema = z.object({
  agreement_start_date: z.string().nullable().or(z.string().date()),
  agreement_end_date: z.string().nullable().or(z.string().date()),
  booking_contract: z.number(),
  account_name: z.string(),
  calculated_sw: z.number().min(0),
  calculated_hw: z.number().min(0),
  booked_theater_id: z.number().min(0),
  sold_as_service_type_id: z.number().min(0),
  sold_as_pricing_type_id: z.number().min(0),
  buying_program_type_id: z.number().min(0),
  is_renewal: z.boolean(),
  assignments: SortedBookingUserAssignmentSchema,
  is_current_and_unassigned: truthyBool,
});

export const ModifyVerifiedBookingSchema = z.object({
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
  booked_theater_id: z.number().min(1),
  sold_as_service_type_id: z.number().min(1),
  sold_as_pricing_type_id: z.number().min(1),
  buying_program_type_id: z.number().min(1),
});

export type IVerifiedBookingModifyDcTypes = z.infer<
  typeof ModifyBookingDcTypesSchema
>;

export type IVerifiedBookingResponse = z.infer<
  typeof VerifiedBookingResponseSchema
>;
export type IVerifiedBookingModifyCalculated = z.infer<
  typeof ModifyVerifiedBookingSchema
>;
export type IModifyBookingUserAssignment = z.infer<
  typeof ModifyBookingUserAssignmentSchema
>;

export type IUserAssignment = z.infer<typeof BookingUserAssignmentSchema>;
