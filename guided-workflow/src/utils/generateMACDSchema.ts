import { z, ZodBoolean, ZodObject, ZodRawShape, ZodTypeAny } from "zod";

import { CellString } from "~/domain/grids/Cell";
import {
  TMACDToolSchemaItemResponse,
  TMACDToolSchemaSingleItemResponse,
} from "~/domain/MACD";

import { buildSchema } from "./buildCellSchema";

type TMultiSchemas = {
  tool_name: string;
  tool_action: string;
  zodSchemas: ZodObject<ZodRawShape>[];
  schemaKey: `${string}_${string}`;
  dateCols: string[];
};

type TToolSchema<Schema extends TMACDToolSchemaSingleItemResponse> = {
  title: string;
  tool_name: string;
  tool_action: string;
  zodSchema: ZodObject<ZodRawShape>;
  schema: Schema;
  schemaKey: `${string}_${string}`;
  dateCols: string[];
};

type TToolMultiSchema<Schema extends TMACDToolSchemaItemResponse> = {
  title: string;
  tool_name: string;
  tool_action: string;
  zodSchema: ZodTypeAny;
  schema: Schema;
  schemaKey: `${string}_${string}`;
  dateCols: string[];
};

type TSchemaField =
  | typeof CellString
  | z.ZodOptional<typeof CellString>
  | ZodBoolean
  | z.ZodOptional<ZodBoolean>;

export const parseToolSchema = <Schema extends TMACDToolSchemaItemResponse>(
  schema: Schema,
): TToolMultiSchema<Schema> => {
  if ("anyOf" in schema) {
    const definitions = Object.values(schema.definitions)
      .map((s) => generateZodSchema(s))
      .reduce<TMultiSchemas>(
        (acc, d) => {
          if (!acc.tool_name) acc.tool_name = d.tool_name;
          if (!acc.tool_action) acc.tool_action = d.tool_action;
          if (acc.schemaKey === "_") acc.schemaKey = d.schemaKey;

          acc.zodSchemas.push(d.zodSchema);
          acc.dateCols.push(...d.dateCols);
          return acc;
        },
        {
          tool_name: "",
          tool_action: "",
          schemaKey: "_",
          dateCols: [],
          zodSchemas: [],
        },
      );

    return {
      title: schema.title,
      tool_name: definitions.tool_name,
      tool_action: definitions.tool_action,
      schema,
      schemaKey: definitions.schemaKey,
      zodSchema: z.union(
        definitions.zodSchemas as unknown as [
          ZodTypeAny,
          ZodTypeAny,
          ...ZodTypeAny[],
        ],
      ),
      dateCols: definitions.dateCols,
    };
  }

  const { tool_action, tool_name, title, zodSchema, schemaKey, dateCols } =
    generateZodSchema(schema);

  return {
    tool_action,
    tool_name,
    title,
    zodSchema,
    schemaKey,
    dateCols,
    schema,
  };
};

/**
 * Generates a Zod schema from a MACD tool schema item response. We copy the tool_name and tool_action properties, (retrieving their default values from the schema) and move them to the top level of the generated schema.
 * @param schema
 */

export const generateZodSchema = <
  Schema extends TMACDToolSchemaSingleItemResponse,
>(
  schema: Schema,
): TToolSchema<Schema> => {
  const zodShape: Record<string, TSchemaField> = {};

  const {
    tool_name: tool_name_prop,
    tool_action: tool_action_prop,
    ...properties
  } = schema.properties;

  const dateCols: string[] = [];

  for (const [key, value] of Object.entries(properties)) {
    const required = schema.required.includes(key);

    zodShape[key] = buildSchema(
      value.format || value.type,
      value.title,
      required,
    );

    if (value.format === "date") {
      dateCols.push(key);
    }
  }

  const zodSchema = z.object(zodShape);

  return {
    title: schema.title,
    tool_name: tool_name_prop.default,
    tool_action: tool_action_prop.default,
    zodSchema,
    schema: schema,
    schemaKey: `${tool_name_prop.default}_${tool_action_prop.default}`,
    dateCols,
  };
};
