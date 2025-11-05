import { z } from "zod";

import ManagedContractSchema, {
  ManagedContract,
  ManagedContractPostSchema,
} from "./Managed";
import { truthyEnum } from "./Truthy";

export type IResponsibleUser = z.infer<typeof ResponsibleUsersSchema>;
export type IBookingsContract = z.infer<typeof BookingsContractsSchema>;
export type IBookingContractPost = z.infer<typeof BookingContractPostSchema>;

const safeManagedContractSchema: z.ZodType<
  ManagedContract[],
  z.ZodTypeDef,
  unknown
> = z.array(z.unknown()).transform((contracts) => {
  return contracts
    .filter((c) => ManagedContractSchema.safeParse(c).success)
    .map((c) => ManagedContractSchema.parse(c));
});

export const ResponsibleUsersSchema = z.object({
  is_block_owner: truthyEnum, //    Whether the logged-in user is able to unlink / edit the managed contracts
  managed_contracts: z.object({
    contracts: z.lazy(() => safeManagedContractSchema),
  }),
  responsible_user: z.number(), //   User ID
  responsible_user_cco: z.string(), // Email address
});

const BookingsContractsBaseSchema = z.object({
  account_name: z.string(),
  agreement_end_date: z.string().nullable(),
  agreement_start_date: z.string().nullable(),
  booking_contract: z.number(),
  dc_engagement_id: z.number(),
  sold_as_buying_program: z.string().default("NONE"),
  sold_as_pricing_model: z.string().default("NONE"),
  sold_as_service_name: z.string().default("UNKNOWN"),
});

export const BookingsContractsSchema = BookingsContractsBaseSchema.extend({
  responsible_users: z.array(ResponsibleUsersSchema),
  effective_end_date: z.string().nullable(),
});

export const BookingContractPostSchema = z.object({
  booking_contract: z.number(),
  dc_engagement_id: z.number(),
  account_name: z.string(),
  agreement_start_date: z.string().nullable(),
  agreement_end_date: z.string().nullable(),
  managed_contracts: z.array(ManagedContractPostSchema),
});

export const BookingsContractResponseSchema = z.array(BookingsContractsSchema);

export const parseBookingsContracts = (
  data: unknown,
): Promise<IBookingsContract[]> => {
  return BookingsContractResponseSchema.parseAsync(data);
};

export const ManagedContractBodySchema = z.object({
  booking_contract: z.number(),
  dc_user_id: z.number(),
  dc_engagement_id: z.number(),
});

export type IManagedContractBody = z.infer<typeof ManagedContractBodySchema>;
