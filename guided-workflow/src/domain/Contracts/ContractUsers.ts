import { z } from "zod";

export const ContractUserSchema = z.object({
  user_id: z.number(),
  display_name: z.string(),
  cisco_cco_id: z.string(),
  user_title: z.string(),
  is_direct_report: z.boolean(),
  theater: z.string(),
  total_utilization: z.number(),
  starting_bookings: z.number(),
  expiring_bookings: z.number(),
  projected_utilization: z.number(),
});

export type IContractUser = z.infer<typeof ContractUserSchema>;
