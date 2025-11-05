import { z, ZodObject, ZodRawShape, ZodUnion } from "zod";

import { DateFormatEnum } from "./grids/Cell";

const DataTypeEnumSchema = z.enum([
  "string",
  "number",
  "integer",
  "boolean",
  "null",
]);
const DataFormatEnumSchema = z.enum(["date"]);

export type TSchemaDataType = z.infer<typeof DataTypeEnumSchema>;
export type TDataFormatEnum = z.infer<typeof DataFormatEnumSchema>;

type EnumDefaultMatch<T extends { default: string; enum: string[] }> = T & {
  enum: readonly [T["default"]];
};

type TRequiredProperties<
  T extends { properties: Record<string, unknown>; required: string[] },
> = T & { required: (keyof T["properties"])[] };

// These are used as enums on the API. They don't translate well to JSON schema
const MACDIdentifierPropertySchema = z
  .object({
    type: z.literal("string"),
    default: z.string(),
    enum: z.array(z.string()).refine((val) => val.length === 1),
  })
  .superRefine((data, ctx): data is EnumDefaultMatch<typeof data> => {
    if (data.enum[0] !== data.default) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: "The enum value must match the default value",
        path: ["enum"],
      });
    }
    return z.NEVER;
  });

// Represents all other properties in the schema
export const MACDToolSchemaProperty = z.object({
  title: z.string(),
  description: z.string().nullish(),
  type: DataTypeEnumSchema,
  default: z.union([z.string(), z.number(), z.null(), z.undefined()]).nullish(),
  format: DataFormatEnumSchema.nullish(),
});

const MACDToolSchemaPropertiesEnums = z.object({
  tool_name: MACDIdentifierPropertySchema,
  tool_action: MACDIdentifierPropertySchema,
});

const MACDToolSchemaProperties = MACDToolSchemaPropertiesEnums.catchall(
  MACDToolSchemaProperty,
);
export type TMACDToolSchemaProperties = z.infer<
  typeof MACDToolSchemaProperties
>;

export const MACDToolSchemaSingleItemResponse = z
  .object({
    title: z.string(),
    type: z.literal("object"),
    properties: MACDToolSchemaProperties,
    required: z.array(z.string()),
  })
  .superRefine((data, ctx): data is TRequiredProperties<typeof data> => {
    const { properties, required } = data;
    const missingRequiredProperties = required.filter(
      (prop) => !(prop in properties),
    );
    if (missingRequiredProperties.length) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: `Required properties mentions ${missingRequiredProperties.join(", ")}, but they are not present in properties`,
      });
    }
    return z.NEVER;
  });

export type TMACDToolSchemaSingleItemResponse = z.infer<
  typeof MACDToolSchemaSingleItemResponse
>;

export const MACDToolSchemaAnyOf = z.array(
  z.object({
    $ref: z.string(),
  }),
);

export const MACDToolSchemaMultiItemResponse = z.object({
  title: z.string(),
  anyOf: MACDToolSchemaAnyOf,
  definitions: z.record(z.string(), MACDToolSchemaSingleItemResponse),
});

export type TMACDToolSchemaMultiItemResponse = z.infer<
  typeof MACDToolSchemaMultiItemResponse
>;

export const MACDToolSchemaItemResponse = z.union([
  MACDToolSchemaSingleItemResponse,
  MACDToolSchemaMultiItemResponse,
]);

export type TMACDToolSchemaItemResponse = z.infer<
  typeof MACDToolSchemaItemResponse
>;

export const MACDToolSchemaAPIResponse = z.array(MACDToolSchemaItemResponse);

export type TMACDToolSchemaProperty = z.infer<typeof MACDToolSchemaProperty>;
export type TMACDToolSchemaAPIResponse = z.infer<
  typeof MACDToolSchemaAPIResponse
>;

export type TZodObjectSchema = ZodObject<ZodRawShape>;
export type TZodUnionSchema = ZodUnion<
  [TZodObjectSchema, ...TZodObjectSchema[]]
>;
export type TMACDZodSchema = TZodObjectSchema | TZodUnionSchema;
export type TMACDToolSchemas = {
  title: string;
  tool_name: string;
  tool_action: string;
  zodSchema: TMACDZodSchema;
  schema: TMACDToolSchemaItemResponse;
  schemaKey: `${string}_${string}`;
  dateCols: string[];
}[];

export const MACDRowsSchema = z.array(z.record(z.string(), z.unknown()));

// Input Form Types
export const MACDInputFormSchema = z.object({
  tool_name: z.string(),
  tool_action: z.string(),
  notes: z.string().optional(),
  approved_by: z.string(),
  sign_off_identity_id: z.number(),
  effective_date: z.string().date(),
  schemaKey: z.string(),
  date_cols: z.array(z.string()),
});

export const MACDInputDateFormatSchema = z.object({
  date_format: DateFormatEnum,
});

export const MACDInputReviewSchema = z.object({
  isSubmitting: z.boolean(),
});

export const MACDInputWorkflowSchema = MACDInputFormSchema.merge(
  MACDInputDateFormatSchema,
).merge(MACDInputReviewSchema);

export type TMACDInputForm = z.infer<typeof MACDInputFormSchema>;
export type TMACDRows = z.infer<typeof MACDRowsSchema>;
export type TMACDInputReview = z.infer<typeof MACDInputReviewSchema>;
export type TMACDInputWorkflow = z.infer<typeof MACDInputWorkflowSchema>;

export const MACDInputPostSchema = z.object({
  tool_name: z.string(),
  tool_action: z.string(),
  notes: z.string().optional(),
  approved_by: z.string().optional(),
  sign_off_identity_id: z.number().optional(),
  effective_date: z.string().optional(),
  dc_engagement_id: z.number(),
  rows: MACDRowsSchema,
});

export type TMACDInputPost = z.infer<typeof MACDInputPostSchema>;

export const MACDInputItemResponseSchema = z.object({
  request_id: z.number(),
  dc_engagement_id: z.number(),
  dc_user_id: z.number(),
  row_count: z.number(),
  approved_by: z.string().nullable(),
  sign_off_identity_id: z.number().nullable(),
  effective_date: z.string().nullable(),
  tool_name: z.string(),
  tool_action: z.string(),
  notes: z.string().nullable(),
  created_by: z.string(),
  create_dtm: z.string(),
  updated_by: z.string().nullable(),
  update_dtm: z.string().nullable(),
});

export const MACDInputResponseSchema = z.array(MACDInputItemResponseSchema);

export type TMACDInputItemResponse = z.infer<
  typeof MACDInputItemResponseSchema
>;
export type TMACDInputResponse = z.infer<typeof MACDInputResponseSchema>;
