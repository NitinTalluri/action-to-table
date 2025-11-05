/**
 * Generic query key factory for schema inference workflows
 * Creates hierarchical query keys: namespace -> fileName -> sheetName -> operation
 */

import { TSchemaInferenceNamespace } from "./schemaInferenceRegistry";

/**
 * all - base key for all sheet reader queries
 * list - list all sheets for a given file in a given namespace
 * detail - detail for a given sheet in a given file in a given namespace (not intended for direct use)
 * inferenceResult - schema inference result for a given sheet in a given file in a given namespace. Changing sheet name or file name will invalidate this query
 * rawData - raw data for a given sheet in a given file in a given namespace using a schema inference result. Changing sheet name, file name, or schema inference result will invalidate this query
 * validatedData - validated data for a given sheet in a given file in a given namespace using a schema inference result. Changing sheet name, file name, or schema inference result will invalidate this query
 *
 */

type TKeyPrefix = {
  namespace: TSchemaInferenceNamespace;
  fileName: string;
  sheetName: string;
};

export const schemaInferenceQueryKeys = {
  all: ["sheetReader", "schema_inference"] as const,
  // List all sheets for a given file in a given namespace
  list: (namespace: TSchemaInferenceNamespace, fileName: string) =>
    [...schemaInferenceQueryKeys.all, namespace, fileName] as const,
  // Anything here and below is scoped to a specific sheet in a specific file in a specific namespace
  detail: (prefix: TKeyPrefix) => {
    const { namespace, fileName, sheetName } = prefix;
    return [
      ...schemaInferenceQueryKeys.list(namespace, fileName),
      sheetName,
    ] as const;
  },

  inferenceResult: (prefix: TKeyPrefix) => {
    // Result of attempting to pick a schema to resolve
    const { namespace, fileName, sheetName } = prefix;
    return [
      ...schemaInferenceQueryKeys.detail({ namespace, fileName, sheetName }),
      "inference",
    ] as const;
  },
  resolvedData: (prefix: TKeyPrefix) => {
    // Resolved data - data after loading the raw data and applying the inferred schema
    const { namespace, fileName, sheetName } = prefix;
    return [
      ...schemaInferenceQueryKeys.inferenceResult({
        namespace,
        fileName,
        sheetName,
      }),
      "resolved",
    ] as const;
  },
  validatedData: (prefix: TKeyPrefix) => {
    // Validated data - data after user sees and potentially edits DataGrid data, then presses next to proceed to apply zod schema
    const { namespace, fileName, sheetName } = prefix;
    return [
      ...schemaInferenceQueryKeys.resolvedData({
        namespace,
        fileName,
        sheetName,
      }),
      "validated",
    ] as const;
  },
};
