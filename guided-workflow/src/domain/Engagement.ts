import { z } from "zod";

import { Booleanized } from "../types/base";
import { truthyEnum } from "./Contracts";

export const EngagementResponseSchema = z.object({
  created_by: z.string(),
  create_dtm: z.string(),
  update_dtm: z.string().nullable(),
  updated_by: z.string().nullable(),
  is_deleted: truthyEnum,
  dc_engagement_id: z.number(),
  engagement_name: z.string(),
  is_sfc: truthyEnum,
  is_cxea: truthyEnum,
  is_software: truthyEnum,
  sfc_agreement_type: z.number(),
  notes: z.string(),
});

export type TEngagementResponse = z.infer<typeof EngagementResponseSchema>;

export type TEngagement = Booleanized<TEngagementResponse>;

export const DeletedEngagementSchema = z.object({
  dc_engagement_id: z.number(),
  engagement_name: z.string(),
  engagement_notes: z.string().nullish(),
  update_dtm: z.string(),
  updated_by: z.string(),
});

export type TDeletedEngagement = z.infer<typeof DeletedEngagementSchema>;

export const LinkSchema = z.object({
  id: z.coerce.number(),
  dc_engagement_id: z.coerce.number(),
  link_type: z.enum(["acat_links", "mce_links", "party_links", "smart_links"]),
  last_updated: z.string().nullish(),
});

export type TLink = z.infer<typeof LinkSchema>;

export const EngagementLinksSchema = z.object({
  acat_links: z.array(
    LinkSchema.refine((arg) => arg.link_type === "acat_links"),
  ),
  mce_links: z.array(LinkSchema.refine((arg) => arg.link_type === "mce_links")),
  party_links: z.array(
    LinkSchema.refine((arg) => arg.link_type === "party_links"),
  ),
  smart_links: z.array(
    LinkSchema.refine((arg) => arg.link_type === "smart_links"),
  ),
});

export type TEngagementLinks = z.infer<typeof EngagementLinksSchema>;

export const EngagementOwnersResponseSchema = z.array(
  z.object({
    user_id: z.number(),
    cisco_cco_id: z.string(),
    user_title: z.string(),
  }),
);

export type TEngagementOwners = z.infer<typeof EngagementOwnersResponseSchema>;
