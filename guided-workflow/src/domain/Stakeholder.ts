import { z } from "zod";

import { truthyEnum } from "~/domain/Contracts";

const stakeholderCreateSchema = z.object({
  stakeholder_type_id: z.coerce.number(),
  dc_engagement_id: z.number(),
  stakeholder_name: z.string(),
  stakeholder_email: z.string(),
  stakeholder_phone: z.string().catch(""),
});

export const StakeholderSchema = z.object({
  stakeholder_id: z.number(),
  stakeholder_type_id: z.number(),
  stakeholder_name: z.string().nullable(),
  stakeholder_email: z.string().nullable(),
  stakeholder_phone: z.string().nullable(),
  dc_engagement_id: z.number(),
  is_deleted: truthyEnum,
  created_by: z.string().nullable(),
  create_dtm: z.string().nullable(),
  update_dtm: z.string().nullable(),
  updated_by: z.string().nullable(),
});

export const parseStakeholderFormValues = (
  values: IStakeholderFormValues,
  dc_engagement_id: number,
): IStakeholderCreate => {
  return stakeholderCreateSchema.parse({
    ...values,
    dc_engagement_id,
  });
};

export const parseStakeholders = (stakeholder: unknown[]): IStakeholder[] => {
  return z.array(StakeholderSchema).parse(stakeholder);
};

export type IStakeholderCreate = z.infer<typeof stakeholderCreateSchema>;
export type IStakeholder = z.infer<typeof StakeholderSchema>;
export type IStakeholderFormValues = Omit<
  IStakeholderCreate,
  "dc_engagement_id"
>;
