import { type CellObject, utils, type WorkSheet } from "xlsx";

import {
  TColumnSchema,
  TResolvedColumn,
  TUnresolvedColumn,
} from "~/domain/ColumnResolver";
import {
  arrayDateTransformer,
  arrayMapper,
  TMapper,
} from "~/hooks/upload/useExcelReader/common";
import invariant from "~/utils/invariant";

type TNormalizedName = {
  rank: number; // Lower rank means higher priority
  name: string; // The normalized name
};

interface IProcessedColumn {
  displayName: string; // Name of the column as it appears in the header row
  normalizedDisplayNames: TNormalizedName[]; // Normalized names of increasing level of normalization
  resolvedSchema: TColumnSchema | null; // The schema that matches the column, or null if no schema matches
  index: number; // The index of the column in the header row
}

type TResolverFunction = (
  worksheet: WorkSheet,
  schemaColumns: TColumnSchema[],
) => {
  resolvedColumns: TResolvedColumn[];
  unresolvedColumns: TUnresolvedColumn[];
};

const lowerCase = (name: string): string => {
  return name.toLowerCase();
};
const trim = (name: string): string => {
  return name.trim();
};
const replaceSpacesWithUnderscores = (name: string): string => {
  return name.replace(/\s+/g, "_"); // Replace spaces with underscores
};
const removeSpecialCharacters = (name: string): string => {
  return name.replace(/[^a-z0-9_]/g, ""); // Remove special characters except underscore
};

const normalizeSteps = [
  lowerCase,
  trim,
  replaceSpacesWithUnderscores,
  removeSpecialCharacters,
];

const applyNormalizationSteps = (
  name: string,
  steps: ((name: string) => string)[],
): TNormalizedName[] => {
  let normalizedName = name;
  return steps.map((step, rank) => {
    normalizedName = step(normalizedName);
    return { rank, name: normalizedName };
  });
};

export const resolveColumns: TResolverFunction = (worksheet, schemaColumns) => {
  const processedColumns: IProcessedColumn[] = [];
  const headerRowValues: string[] = [];

  if (!worksheet || !worksheet["!ref"] || !worksheet["!data"]) {
    console.error("resolveColumns: Invalid worksheet data");
    return {
      resolvedColumns: [],
      unresolvedColumns: [],
      error: "Invalid worksheet data",
    };
  }

  const range = utils.decode_range(worksheet["!ref"]);
  const headerRowNum = range.s.r; // Assuming header is the first row in the range
  const headerRow = worksheet["!data"][headerRowNum];

  for (let C = range.s.c; C <= range.e.c; ++C) {
    const cell = headerRow[C] as CellObject | undefined;
    if (!cell || !cell.v) {
      continue;
    }
    const cellValue = typeof cell.v !== "undefined" ? String(cell.v) : "";

    if (cellValue.trim() === "") {
      continue;
    }

    headerRowValues.push(cellValue);
    processedColumns.push({
      displayName: cellValue,
      normalizedDisplayNames: applyNormalizationSteps(
        cellValue,
        normalizeSteps,
      ),
      resolvedSchema: null,
      index: C,
    });
  }

  const aliasToCanonicalNameMap = new Map<string, string>(); // Column aliases to name

  for (let stepNum = 0; stepNum < normalizeSteps.length; stepNum++) {
    for (const sc of schemaColumns) {
      const { name, displayName, aliases } = sc;
      const normalizedNames = applyNormalizationSteps(
        name,
        normalizeSteps.slice(0, stepNum + 1),
      );
      const normalizedDisplayNames = applyNormalizationSteps(
        displayName,
        normalizeSteps.slice(0, stepNum + 1),
      );
      const normalizedAliases = aliases.flatMap((alias) =>
        applyNormalizationSteps(alias, normalizeSteps.slice(0, stepNum + 1)),
      );
      for (const normalizedName of normalizedNames) {
        if (!aliasToCanonicalNameMap.has(normalizedName.name)) {
          aliasToCanonicalNameMap.set(normalizedName.name, name);
        }
      }
      for (const normalizedDisplayName of normalizedDisplayNames) {
        if (!aliasToCanonicalNameMap.has(normalizedDisplayName.name)) {
          aliasToCanonicalNameMap.set(normalizedDisplayName.name, name);
        }
      }
      for (const normalizedAlias of normalizedAliases) {
        if (!aliasToCanonicalNameMap.has(normalizedAlias.name)) {
          aliasToCanonicalNameMap.set(normalizedAlias.name, name);
        }
      }
    }
  }

  const usedSchemaNames = new Set<string>(); // Track which schema names have been used to avoid duplicates

  // First pass: Try to exact match with no normalization
  for (const pc of processedColumns) {
    const name = pc.displayName;
    const canonicalName = aliasToCanonicalNameMap.get(name);
    if (!canonicalName) continue;
    if (usedSchemaNames.has(canonicalName)) {
      continue; // Schema already used
    }
    const matchedSchemaColumn = schemaColumns.find(
      (sc) => sc.name === canonicalName,
    );
    invariant(
      matchedSchemaColumn,
      "Should have found a matching schema column",
    );
    pc.resolvedSchema = matchedSchemaColumn;
    usedSchemaNames.add(canonicalName);
  }

  // Loop through processedColumns and try to resolve them against schemaColumns step-by-step
  for (let stepNum = 0; stepNum < normalizeSteps.length; stepNum++) {
    // First pass: Try to match by exact normalized name or normalized display name
    for (const pc of processedColumns) {
      const normalizedDisplayName = pc.normalizedDisplayNames[stepNum].name;
      if (!normalizedDisplayName) {
        continue;
      }
      const canonicalName = aliasToCanonicalNameMap.get(normalizedDisplayName);
      if (!canonicalName) {
        continue;
      }
      if (usedSchemaNames.has(canonicalName)) {
        continue; // Schema already used
      }
      // Find the schema column that matches this canonical name
      const matchingSchemaColumn = schemaColumns.find(
        (sc) => sc.name === canonicalName,
      );
      invariant(
        matchingSchemaColumn,
        "Should have found a matching schema column",
      );
      pc.resolvedSchema = matchingSchemaColumn;
      usedSchemaNames.add(canonicalName);
    }
  }
  const resolvedColumnsResult: TResolvedColumn[] = [];
  const unresolvedColumnsResult: TUnresolvedColumn[] = [];

  for (const pc of processedColumns) {
    if (pc.resolvedSchema) {
      resolvedColumnsResult.push({
        displayName: pc.displayName,
        index: pc.index,
        resolvedSchema: pc.resolvedSchema,
      });
    } else {
      unresolvedColumnsResult.push({
        displayName: pc.displayName,
        index: null,
        resolvedSchema: null,
      });
    }
  }

  return {
    resolvedColumns: resolvedColumnsResult,
    unresolvedColumns: unresolvedColumnsResult,
  };
};

export const extractDataFromResolved = (
  worksheet: WorkSheet,
  resolvedColumns: TResolvedColumn[],
) => {
  /**
   * Get the header row from the worksheet
   * Then, using the resolvedColumns, build an index to resolved column name
   */

  const mapperColumns: TMapper[] = resolvedColumns
    .sort((a, b) => a.index - b.index)
    .map((col) => ({
      index: col.index,
      key: col.resolvedSchema.name,
    }));

  const rowMapper = arrayMapper(mapperColumns);
  const rows: unknown[][] = utils.sheet_to_json(worksheet, {
    header: 1,
    defval: null,
    UTC: true,
  });
  const dataRows = rows.slice(1); // Skip the header row
  return dataRows.map(arrayDateTransformer).map(rowMapper);
};
