import { z } from "zod";

// Schema for individual super_customer object
const SuperCustomerSchema = z.object({
  super_customer_id: z.number(),
  super_customer_name: z.string(),
  dc_engagement_ids: z.array(z.number()),
});

// Schema for the enagement names
const EngagementNamesSchema = z.record(z.string(), z.string());

// Schema for available engagement IDs
const AvailableEngagementIdsSchema = z.array(z.number());

// Schema for available super customer names
const SuperCustomerNamesSchema = z.array(z.string());

// Schema for the super customer list response
export const SuperCustomerListResponseSchema = z.object({
  super_customers: z.array(SuperCustomerSchema),
  names: EngagementNamesSchema,
  available_dc_engagement_ids: AvailableEngagementIdsSchema,
});

export const SuperCustomerFormSchema = z.object({
  super_customer_id: z.number().optional(),
  super_customer_name: z
    .string()
    .trim()
    .min(1, "Parent Customer name is required")
    .regex(/^[a-zA-z0-9_ ]+$/, "Invalid Parent Customer name."),
  dc_engagement_ids: z
    .array(z.number())
    .transform((data) => Array.from(new Set(data))),
});

export type TEngagementIDs = z.infer<typeof AvailableEngagementIdsSchema>;

export type TEngagementNames = z.infer<typeof EngagementNamesSchema>;

export type TSuperCustomerItemResponse = z.infer<typeof SuperCustomerSchema>;

export type TSuperCustomerListResponse = z.infer<
  typeof SuperCustomerListResponseSchema
>;

export type TSuperCustomerForm = z.infer<typeof SuperCustomerFormSchema>;

export type TSuperCustomerNames = z.infer<typeof SuperCustomerNamesSchema>;
