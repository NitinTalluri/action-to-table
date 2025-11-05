import { z } from "zod";

export const UserDefinedTypeFieldNames = z.enum([
  "collector-file-name",
  "customer-file-name",
]);

export type TUserDefinedTypeFieldNames = z.infer<
  typeof UserDefinedTypeFieldNames
>;
export const UserDefinedType = z.object({
  id: z.number(),
  value: z.coerce.string(),
  field_name: z.string(),
  dc_engagement_id: z.number(),
});

export const UserDefinedTypeUpdateResponse = UserDefinedType.merge(
  z.object({
    originalId: z.number(),
  }),
);

export type TUserDefinedType = z.infer<typeof UserDefinedType>;

export const UserDefinedTypeArray = z.array(UserDefinedType);
export type TUserDefinedTypeArray = z.infer<typeof UserDefinedTypeArray>;

export const UserDefinedTypeCreate = z.object({
  value: z.string(),
  field_name: UserDefinedTypeFieldNames,
  dc_engagement_id: z.number(),
});
export type TUserDefinedTypeCreate = z.infer<typeof UserDefinedTypeCreate>;

export const UserDefinedTypeUpdate = z.object({
  value: z.string(),
  id: z.number(),
  dc_engagement_id: z.number(),
});
export type TUserDefinedTypeUpdate = z.infer<typeof UserDefinedTypeUpdate>;

export const UserDefinedTypeDelete = z.object({
  id: z.number(),
  dc_engagement_id: z.number(),
});
export type TUserDefinedTypeDelete = z.infer<typeof UserDefinedTypeDelete>;
