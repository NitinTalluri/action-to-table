import { utils, WorkSheet } from "xlsx";

import {
  ISchemaInferenceResult,
  SchemaInferenceNamespace,
  schemaRegistry,
  TSchemaInferenceNamespace,
} from "~/domain/resolvers/schemaInferenceRegistry";
import {
  arrayDateTransformer,
  arrayMapper,
  extractHeadersFromSheet,
  objectFieldChecker,
  TMixedMapper,
} from "~/hooks/upload/useExcelReader/common";
import { TSuccessfulSchemaInferenceResult } from "~/hooks/upload/useExcelReader/schemaSheetReaderTypes";
import invariant from "~/utils/invariant";

const registerNamespaceSchema = async (
  namespace: TSchemaInferenceNamespace,
) => {
  switch (namespace) {
    case SchemaInferenceNamespace.enum.collector: {
      const { loadCollectorSchemas } = await import(
        "~/features/workflows/uploads/collector-file/domain/collectorSchemaInference"
      );
      const collectorJsonSchemas = loadCollectorSchemas();
      console.log(
        `Registering ${collectorJsonSchemas.length} schemas for namespace: ${namespace}`,
      );
      collectorJsonSchemas.forEach(({ schema, external }) => {
        schemaRegistry.addJsonSchema(
          schema.schemaName,
          schema.displayName,
          schema.jsonSchema,
          external,
          SchemaInferenceNamespace.enum.collector,
        );
      });
      return namespace;
    }
  }
};

/**
 * Handle schema inference request
 */
export const inferSchema = async <
  T extends TSchemaInferenceNamespace = TSchemaInferenceNamespace,
>(
  sheet: WorkSheet,
  namespace: TSchemaInferenceNamespace,
): Promise<ISchemaInferenceResult<T>> => {
  await registerNamespaceSchema(namespace);
  const headers = extractHeadersFromSheet(sheet);
  const inferenceResult = schemaRegistry.inferJsonSchema(headers, namespace);

  // Handle case where no schema was found at all
  if (!inferenceResult.schemaName) {
    // Construct meaningful error message for no schema found
    const headersList = headers.length > 0 ? headers.join(", ") : "no columns";
    const errorMessage = `No compatible schema found. Your spreadsheet contains: ${headersList}.`;

    return {
      ...inferenceResult,
      schemaName: null,
      isCompatible: false,
      errorMessage,
    };
  }

  // Enforce compatibility check - schema is incompatible if any non-nullable required fields are missing
  if (inferenceResult.schemaName && !inferenceResult.isCompatible) {
    // Calculate which fields are non-nullable required (for the error message)
    const missingNonNullableFields = inferenceResult.missingRequired.filter(
      (field) => !inferenceResult.missingOptionalFields.includes(field),
    );

    const schemaEntry = schemaRegistry.getJsonSchemaInNamespace(
      inferenceResult.schemaName,
      namespace!,
    );

    invariant(
      schemaEntry,
      `Schema ${inferenceResult.schemaName} not found in namespace ${namespace}`,
    );

    const schemaDisplayName = `${schemaEntry.displayName} (${inferenceResult.schemaName})`;

    // Get display names for missing non-nullable fields
    const missingFieldDisplayNames = missingNonNullableFields.map((field) => {
      const fieldDef = schemaEntry.jsonSchema[field];
      return fieldDef?.displayName
        ? `${fieldDef.displayName} (${field})`
        : field;
    });

    // Get display names for successfully mapped fields
    const mappedFieldDisplayNames = Object.entries(inferenceResult.mapping).map(
      ([header, schemaField]) => {
        const fieldDef = schemaEntry.jsonSchema[schemaField];
        return fieldDef?.displayName
          ? `${fieldDef.displayName} (${schemaField})`
          : `${header} (${schemaField})`;
      },
    );

    const errorMessage =
      `Your spreadsheet most closely resembles the ${schemaDisplayName} schema.\n` +
      `While it contains ${mappedFieldDisplayNames.join(", ")}, it's missing these required columns: ${missingFieldDisplayNames.join(", ")}.`;

    // Return failed result instead of throwing
    return {
      ...inferenceResult,
      schemaName: null,
      isCompatible: false,
      errorMessage,
    };
  }
  if (
    inferenceResult.schemaName &&
    inferenceResult.missingOptionalFields.length > 0
  ) {
    console.info(
      `Schema '${inferenceResult.schemaName}' is compatible: Missing nullable fields will be populated with null values: ${inferenceResult.missingOptionalFields.join(", ")}`,
    );
  }

  return inferenceResult;
};

type TG = ReturnType<typeof getResolvedDataFromInference>;

const resolveDataFromInference = (
  sheet: WorkSheet,
  inferenceResult: TSuccessfulSchemaInferenceResult,
) => {
  const { indexMapping: fieldToIndex, missingOptionalFields } = inferenceResult;

  // We have a mapping `indexMapping` that allows us to map schema fields to column indices
  // And we have a list of `missingOptionalFields` that need to be included as object keys with null values
  // We'll use arrayMapper along with instructions to build a single function that maps row arrays to our desired object shape

  const mapperColumns = Object.entries(fieldToIndex).map(([key, index]) => ({
    key,
    index,
  }));
  const placeholderColumns = missingOptionalFields.map((key) => ({
    key,
    defaultValue: null,
  }));
  const fullMapping: TMixedMapper<null>[] = [
    ...mapperColumns,
    ...placeholderColumns,
  ];
  const rowMapper = arrayMapper(fullMapping);
  const rows: unknown[][] = utils.sheet_to_json(sheet, {
    header: 1,
    defval: null,
    UTC: true,
  });
  const dataRows = rows.slice(1); // Skip the header row
  return dataRows.map(arrayDateTransformer).map(rowMapper);
};

/**
 * Wraps resolveDataFromInference and performs basic validation using required fields.
 * It drops rows where a required field is null. Since we can control what the defval
 * when using SheetJs, empty cells will be represented as nulls.
 * We also include a summary of what was dropped
 * @param sheet
 * @param inferenceResult
 */

type TResolvedResult = {
  rows: Record<string, unknown>[];
  droppedRowCount: number;
};

export const getResolvedDataFromInference = (
  sheet: WorkSheet,
  inferenceResult: TSuccessfulSchemaInferenceResult,
): TResolvedResult => {
  const dataRows = resolveDataFromInference(sheet, inferenceResult);
  const { requiredFields } = inferenceResult;
  const checkRequireFields = objectFieldChecker(requiredFields);
  const validDataRows = dataRows.filter(checkRequireFields);
  const droppedRowCount = dataRows.length - validDataRows.length;
  return {
    rows: validDataRows,
    droppedRowCount,
  };
};
