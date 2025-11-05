import { useMemo } from "react";
import { z } from "zod";

export const dcTypeMapSchema = z.object({
  id: z.number(),
  value: z.string(),
  is_deleted: z.boolean(),
  extra: z.record(z.any()).nullish(),
});

export const dcTypeBookingTypeExtraSchema = z.object({
  is_prospective: z.boolean(),
  is_budgeted: z.boolean(),
});

export const dcTypeAnchorDateIteratorExtraSchema = z.object({
  is_direct: z.boolean(),
});

export const dcTableSchema = z.object({
  table_name: z.string(),
  mappings: z.array(dcTypeMapSchema),
});

export const dcTypesSchema = z.array(dcTableSchema);

export type TDcTypes = z.infer<typeof dcTypesSchema>;
export type TDcTypeMap = z.infer<typeof dcTypeMapSchema>;

export const parseDcTypes = (data: unknown[]): TDcTypes => {
  return dcTypesSchema.parse(data);
};

type TOption = {
  id: TDcTypeMap["id"];
  value: TDcTypeMap["value"];
};

export const mappedOptionSchema = (name: string, options: TOption[]) => {
  /**
   * Factory that creates a zod string schema that is validated against the allowed dc_types
   * and returned as an integer
   */

  const optionNames = options.map((option) => option.value);
  const optionMembers = new Set(
    options.map((option) => option.value.toLowerCase()),
  );

  const optionSchema = z
    .string({
      required_error: `${name} is required`,
      invalid_type_error: `${name} must be text`,
    })
    .transform((val) => val.trim())
    .superRefine((val, ctx) => {
      if (!optionMembers.has(val.toLowerCase())) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: `${val} is not a valid ${name}. Allowed values: ${optionNames.join(
            ", ",
          )}`,
        });
      }
      const matchedId = options.find(
        (option) => option.value.toLowerCase() === val.toLowerCase(),
      )?.id;
      if (matchedId === undefined) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: `Invalid ${name}. Allowed values: ${optionNames.join(", ")}`,
        });
      }
    })
    .transform((val) => {
      return options.find(
        (option) => option.value.toLowerCase() === val.toLowerCase(),
      )!.id;
    });

  type TOptionInputSchema = z.input<typeof optionSchema>;
  type TOptionOutSchema = z.output<typeof optionSchema>;
  type TOptionSchema = z.ZodType<
    TOptionOutSchema,
    z.ZodTypeDef,
    TOptionInputSchema
  >;

  return optionSchema as TOptionSchema;
};

export const useMappedOptionSchema = (
  name: string,
  options: TOption[],
): ReturnType<typeof mappedOptionSchema> => {
  const schema = useMemo(() => {
    return mappedOptionSchema(name, options);
  }, [name, options]);

  return schema;
};
