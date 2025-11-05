import { z } from "zod";

// booked_sw and booked_hw are stored as percentages in the database
// i.e. 100 = 100%

export const UnverifiedBookingResponseSchema = z.object({
  booking_contract: z.coerce.number(),
  booked_sw: z.coerce.number(),
  booked_hw: z.coerce.number(),
  account_name: z.string().catch(""),
  booked_theater_id: z.number().gte(0).nullable(),
  sold_as_service_type_id: z.number().gte(0).nullable(),
  sold_as_pricing_type_id: z.number().gte(0).nullable(),
  buying_program_type_id: z.number().gte(0).nullable(),
  is_renewal: z.boolean(),
  agreement_start_date: z.string().nullable().or(z.string().date()),
  agreement_end_date: z.string().nullable().or(z.string().date()),
});

export const VerifyBookingSchema = z.object({
  booking_contract: z.coerce.number(),
  booked_sw: z.number().min(0).max(1000),
  booked_hw: z.number().min(0).max(1000),
  account_name: z.string(),
  booked_theater_id: z.number().gte(0),
  sold_as_service_type_id: z.number().gte(0),
  sold_as_pricing_type_id: z.number().gte(0),
  buying_program_type_id: z.number().gte(0),
});

export type IUnverifiedBookingResponse = z.infer<
  typeof UnverifiedBookingResponseSchema
>;

export type IVerifyBooking = z.infer<typeof VerifyBookingSchema>;
