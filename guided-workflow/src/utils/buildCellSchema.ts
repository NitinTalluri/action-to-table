import { z } from "zod";

import {
  CellString,
  floatSuperRefine,
  numberSuperRefine,
  stringSuperRefine,
} from "~/domain/grids/Cell";

export const DataTypeEnumSchema = z.enum([
  "string",
  "number",
  "integer",
  "float",
  "boolean",
  "date",
  "null",
]);
export type TSchemaDataType = z.infer<typeof DataTypeEnumSchema>;

const applyOptionalAndRefine = <T extends z.ZodTypeAny>(
  fieldSchema: T,
  required: boolean,
  superRefineFn?: (
    val: z.infer<T>,
    ctx: z.RefinementCtx,
    required: boolean,
  ) => void,
): T => {
  let schema: z.ZodTypeAny = fieldSchema;

  if (superRefineFn) {
    schema = schema.superRefine((val, ctx) =>
      superRefineFn(val, ctx, required),
    );
  }

  return schema as unknown as T;
};

export const buildSchema = <T extends z.ZodTypeAny>(
  type: TSchemaDataType,
  describe: string,
  required: boolean = false,
): T => {
  let fieldSchema: z.ZodTypeAny = CellString;

  switch (type) {
    case "string":
      fieldSchema = applyOptionalAndRefine(
        fieldSchema,
        required,
        stringSuperRefine,
      );
      break;

    case "date":
      fieldSchema = applyOptionalAndRefine(
        fieldSchema,
        required,
        stringSuperRefine,
      );
      break;

    case "integer":
      fieldSchema = applyOptionalAndRefine(
        fieldSchema,
        required,
        numberSuperRefine,
      );
      break;

    case "number":
      fieldSchema = applyOptionalAndRefine(
        fieldSchema,
        required,
        numberSuperRefine,
      );
      break;

    case "float":
      fieldSchema = applyOptionalAndRefine(
        fieldSchema,
        required,
        floatSuperRefine,
      );
      break;

    case "boolean":
      fieldSchema = applyOptionalAndRefine(fieldSchema, required);
      break;

    case "null":
      fieldSchema = z.preprocess(() => null, z.null());
      break;

    default:
      fieldSchema = applyOptionalAndRefine(
        fieldSchema,
        required,
        stringSuperRefine,
      );
  }

  return fieldSchema.describe(describe) as T;
};
