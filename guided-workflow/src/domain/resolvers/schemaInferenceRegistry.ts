import { z } from "zod";

import invariant from "~/utils/invariant";

// Top-level Schema namespace definitions
export const SchemaInferenceNamespace = z.enum(["collector"]);
export type TSchemaInferenceNamespace = z.infer<
  typeof SchemaInferenceNamespace
>;

// Each namespace has its own set of schema names
export const CollectorSchemaInferenceEnum = z.enum([
  "collector_standard",
  "collector_all",
  "collector_cx_cloud",
]);
// Map namespaces to their schema names
export const SchemaNamesByNamespace = {
  [SchemaInferenceNamespace.enum.collector]: CollectorSchemaInferenceEnum,
} as const;

export type TSchemaInferenceName<T> = T extends TSchemaInferenceNamespace
  ? z.infer<(typeof SchemaNamesByNamespace)[T]>
  : never;

type TRequiredRole = "required";
type TOptionalRole = "optional";
type TIgnoredRole = "ignored";

type TSchemaInferenceRequiredField = {
  name: string;
  role: TRequiredRole;
  aliases: string[];
  displayName: string;
  columnName: string;
  default?: never;
};

type TSchemaInferenceOptionalField = {
  name: string;
  role: TOptionalRole;
  aliases: string[];
  displayName: string;
  columnName: string;
  default: string | null;
};

type TSchemaInferenceIgnoredField = {
  name: string;
  role: TIgnoredRole;
  aliases: string[];
  displayName: string;
  columnName: never;
  default?: never;
};

export type TZodAllowedExternalSchemaTypes = z.ZodObject<
  Record<string, z.ZodType<unknown>>
>;

export interface ISchemaInferenceDefinition {
  [K: string]:
    | TSchemaInferenceRequiredField
    | TSchemaInferenceOptionalField
    | TSchemaInferenceIgnoredField;
}

export interface ISchemaInferenceJsonSchema<
  T extends TSchemaInferenceNamespace,
> {
  schemaName: TSchemaInferenceName<T>;
  displayName: string;
  namespace: T;
  jsonSchema: ISchemaInferenceDefinition;
}

export interface ISchemaInferenceResult<
  T extends TSchemaInferenceNamespace = TSchemaInferenceNamespace,
> {
  schemaName: TSchemaInferenceName<T> | null;
  coverage: number; // 0-1 coverage score
  mapping: Record<string, string>; // Display name to schema field name (display purposes)
  indexMapping: Record<string, number>; // Column index to schema field name (parsing purposes)
  missingRequired: string[];
  requiredFields: string[]; // Fields we detected in the spreadsheet that have a role of 'required'. This can be used downstream for rudimentary row validation when loading
  missingOptionalFields: string[]; // Fields that are missing in the spreadsheet, but as they are optional, they can be defaulted
  ignoredColumns: string[]; // Columns that were not mapped to any schema field
  isCompatible: boolean; // Whether the schema is compatible with the headers (all non-nullable required fields present)
  errorMessage?: string; // Error message when inference fails
}

/**
 * Schema Registry Interface
 * Manages schema alias definitions and provides schema inference functionality
 */
export interface ISchemaInferenceRegistry {
  // Add a JSON schema that links to an external (i.e. Zod Schema) definition
  addJsonSchema: <
    T extends TSchemaInferenceNamespace,
    Ext extends TZodAllowedExternalSchemaTypes,
  >(
    schemaName: TSchemaInferenceName<T>,
    displayName: string,
    jsonSchema: ISchemaInferenceDefinition,
    externalSchema: Ext,
    namespace: T,
  ) => void;

  // Get all schemas in a namespace
  getJsonSchemasInNamespace: <T extends TSchemaInferenceNamespace>(
    namespace: T,
  ) => ISchemaInferenceJsonSchema<T>[];

  // Get complete schema entry by name and namespace
  getJsonSchemaInNamespace: <T extends TSchemaInferenceNamespace>(
    schemaName: TSchemaInferenceName<T>,
    namespace: T,
  ) => ISchemaInferenceJsonSchema<T>;

  getExternalSchemaInNamespace: <T extends TSchemaInferenceNamespace>(
    schemaName: TSchemaInferenceName<T>,
    namespace: T,
  ) => TZodAllowedExternalSchemaTypes;

  // Infer schema from headers
  inferJsonSchema: <T extends TSchemaInferenceNamespace>(
    headers: string[],
    namespace: T,
  ) => ISchemaInferenceResult<T>;
}

const devConsole = import.meta.env.DEV
  ? console
  : {
      log: () => {},
      warn: () => {},
      error: () => {},
      group: () => {},
      groupEnd: () => {},
      table: () => {},
    };

/**
 * Helper function to normalize text for comparison
 * Removes spaces, converts to lowercase, etc.
 */
function normalizeText(text: string): string {
  return text
    .toLowerCase()
    .trim()
    .replace(/\s*\(.+\)$/g, "")
    .replace("&", "and")
    .replace(/\s+/g, "_")
    .replace(/[^a-z0-9_]/g, "");
}

/**
 * To determine the level of fit between headers and a potential schema we evaluate:
 * 1. Could all required fields be found? If not, it won't match. We continue looping to provide explanation.
 * 2. Was an optional OR ignored column name found? This adds additional bits of information that further prove a match and can be used in tie-breaks;
 *
 * @param entry
 * @param headers
 * @param normalizedHeaders
 */

const evaluateSchema = <T extends TSchemaInferenceNamespace>(
  entry: ISchemaInferenceJsonSchema<T>,
  headers: string[],
  normalizedHeaders: string[],
): ISchemaInferenceResult<T> => {
  const { schemaName, jsonSchema } = entry;
  const mapping: Map<string, string> = new Map<string, string>();
  const indexMapping: Map<string, number> = new Map(); // Schema field name to column index
  const coveredFields = new Set<string>(); // Fields present in the headers that are present in the schema
  const missingRequired = new Set<string>(); // Required fields missing from the headers
  const missingOptional = new Set<string>(); // Optional fields missing from the headers, present in the schema
  const requiredFields = new Set<string>(); // Fields we detected in the spreadsheet that have a role of 'required'. This can be used downstream for rudimentary row validation when loading

  // For each field in the schema, check if we have a matching header
  for (const [fieldName, fieldDef] of Object.entries(jsonSchema)) {
    const isRequired = fieldDef.role === "required";

    // Check if any header matches this field through aliases
    const possibleMatches = [
      ...new Set(
        [
          ...new Set([
            fieldDef.name,
            fieldDef.displayName,
            ...fieldDef.aliases,
          ]),
        ].map((a) => normalizeText(a)),
      ),
    ];

    // Find any matching header
    const matchedHeaderIndex = normalizedHeaders.findIndex((h) =>
      possibleMatches.some((alias) => alias === h),
    );

    if (matchedHeaderIndex >= 0) {
      // Found a match
      mapping.set(headers[matchedHeaderIndex], fieldName);
      indexMapping.set(fieldName, matchedHeaderIndex);
      devConsole.log(
        `"${headers[matchedHeaderIndex]} - ${matchedHeaderIndex}" --> "${fieldName}"`,
      );
      coveredFields.add(fieldName);
      isRequired && requiredFields.add(fieldName);
    } else if (isRequired) {
      missingRequired.add(fieldName);
    } else {
      missingOptional.add(fieldName);
    }
  }
  // Count fields that should be considered for coverage calculation
  // For this we count the number of matches fields (from worksheet) + required fields (from schema)
  const fieldsForCoverage = Object.entries(jsonSchema).filter(
    ([fieldName, fieldDef]) => {
      // Include field if it's covered (present in the worksheet) OR required
      return (
        coveredFields.has(fieldName) ||
        fieldDef.aliases.some((a) => coveredFields.has(a)) ||
        requiredFields.has(fieldName)
      );
    },
  );

  // Calculate coverage based on fields that should count
  const totalRelevantFields = fieldsForCoverage.length;
  const coverage =
    totalRelevantFields > 0 ? coveredFields.size / totalRelevantFields : 0;

  // Schema is compatible if there are no missing required fields
  const isCompatible = missingRequired.size === 0;

  // Calculate ignored columns - headers that weren't mapped to any schema field

  const mappedHeaders = new Set(mapping.keys());

  const ignoredColumns = headers.filter((header) => !mappedHeaders.has(header));

  const missingRequiredArray = Array.from(missingRequired);
  const missingOptionalFields = Array.from(missingOptional);
  const requiredFieldsArray = Array.from(requiredFields);
  devConsole.table({
    coverage,
    isCompatible,
    requiredFields: requiredFieldsArray.join(", ") || "None",
    missingRequired: missingRequiredArray.join(", ") || "None",
    missingOptionalFields: missingOptionalFields.join(", ") || "None",
    ignoredColumns: ignoredColumns.join(", ") || "None",
  });
  // @ts-expect-error Node/Console types mismatch
  devConsole.groupEnd(`${entry.displayName} ${entry.schemaName}`);
  return {
    schemaName,
    coverage,
    mapping: Object.fromEntries(mapping),
    indexMapping: Object.fromEntries(indexMapping),
    missingRequired: missingRequiredArray,
    requiredFields: requiredFieldsArray,
    missingOptionalFields,
    ignoredColumns,
    isCompatible,
  };
};

/**
 * Find the best schema match for a set of headers
 * Uses header normalization and calculates coverage scores
 */
function findBestSchemaMatch<T extends TSchemaInferenceNamespace>(
  headers: string[],
  schemaEntries: ISchemaInferenceJsonSchema<T>[],
): ISchemaInferenceResult<T> {
  const defaultResult = {
    schemaName: null,
    coverage: 0,
    mapping: {},
    indexMapping: {},
    missingRequired: [],
    requiredFields: [],
    missingOptionalFields: [],
    ignoredColumns: headers,
    isCompatible: false,
    errorMessage: "",
  } satisfies ISchemaInferenceResult<T>;
  if (schemaEntries.length === 0) {
    return {
      ...defaultResult,
      errorMessage: "No schemas available for inference",
    };
  }
  // Normalize headers for matching
  const normalizedHeaders = headers.map((h) => normalizeText(h));
  const results: ISchemaInferenceResult<T>[] = schemaEntries.map((e) => {
    return evaluateSchema(e, headers, normalizedHeaders);
  });

  // Sort by coverage and missing required fields
  const sorted = results.sort((a, b) => {
    // Schemas with all required fields come first
    if (a.missingRequired.length === 0 && b.missingRequired.length > 0)
      return -1;
    if (b.missingRequired.length === 0 && a.missingRequired.length > 0)
      return 1;

    if (a.coverage === b.coverage) {
      // Prefer more data vs less
      const aRealFields = Object.keys(a.mapping).length;
      const aDefaultableFields = a.missingOptionalFields.length;
      const bRealFields = Object.keys(b.mapping).length;
      const bDefaultableFields = b.missingOptionalFields.length;

      if (aRealFields > bRealFields) return -1;
      if (bRealFields > aRealFields) return 1;

      // If same number of real fields, prefer fewer defaultable fields
      if (aDefaultableFields < bDefaultableFields) return -1;
      if (bDefaultableFields < aDefaultableFields) return 1;
    }

    // Then sort by coverage
    return b.coverage - a.coverage;
  });
  return sorted[0];
}

export class SchemaInferenceRegistry implements ISchemaInferenceRegistry {
  private schemas = new Map<
    string,
    ISchemaInferenceJsonSchema<TSchemaInferenceNamespace>
  >();
  private externalSchemas = new Map<
    `${string}-${string}`,
    TZodAllowedExternalSchemaTypes
  >();

  addJsonSchema<T extends TSchemaInferenceNamespace>(
    schemaName: TSchemaInferenceName<T>,
    displayName: string,
    jsonSchema: ISchemaInferenceDefinition,
    externalSchema: TZodAllowedExternalSchemaTypes,
    namespace: T,
  ): void {
    this.schemas.set(schemaName, {
      schemaName,
      displayName,
      namespace,
      jsonSchema,
    });
    const extSchemaKey = `${namespace}-${schemaName}` as const;
    this.externalSchemas.set(extSchemaKey, externalSchema);
  }

  getJsonSchemaInNamespace<T extends TSchemaInferenceNamespace>(
    schemaName: TSchemaInferenceName<T>,
    namespace: T,
  ) {
    const schema = this.schemas.get(schemaName);
    invariant(schema, `Schema ${schemaName} not found in registry`);
    invariant(
      schema.namespace === namespace,
      `Schema ${schemaName} not found in namespace ${namespace}`,
    );
    return schema as ISchemaInferenceJsonSchema<T>;
  }

  getJsonSchemasInNamespace<T extends TSchemaInferenceNamespace>(
    namespace: T,
  ): ISchemaInferenceJsonSchema<T>[] {
    return Array.from(this.schemas.values()).filter(
      (entry) => entry.namespace === namespace,
    ) as ISchemaInferenceJsonSchema<T>[];
  }

  inferJsonSchema<T extends TSchemaInferenceNamespace>(
    headers: string[],
    namespace: T,
  ): ISchemaInferenceResult<T> {
    if (this.schemas.size === 0) {
      devConsole.warn(
        "No schemas registered in the registry. Cannot perform inference.",
      );
    }
    const schemaEntries = this.getJsonSchemasInNamespace(namespace);

    return findBestSchemaMatch<T>(headers, schemaEntries);
  }

  getExternalSchemaInNamespace<T extends TSchemaInferenceNamespace>(
    schemaName: TSchemaInferenceName<T>,
    namespace: T,
  ): TZodAllowedExternalSchemaTypes {
    const extSchemaKey = `${namespace}-${schemaName}` as const;
    const extSchema = this.externalSchemas.get(extSchemaKey);
    invariant(
      extSchema,
      `External schema for ${schemaName} not found in registry`,
    );
    return extSchema;
  }
}

// Create and export singleton instance
export const schemaRegistry = new SchemaInferenceRegistry();
