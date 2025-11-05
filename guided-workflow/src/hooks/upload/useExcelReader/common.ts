import { utils, WorkBook } from "xlsx";

import invariant from "~/utils/invariant";

export const formatIsoDate = (d: Date) => {
  /**
   Convert Date to YYYY-MM-DD format
   */
  return d.toISOString().slice(0, 10); // Extract YYYY-MM-DD from ISO string
};

export const arrayDateTransformer_ =
  (fn: (d: Date) => string) => (arr: unknown[]) =>
    arr.map((item) => (item instanceof Date ? fn(item) : item));

export const arrayDateTransformer = arrayDateTransformer_(formatIsoDate);
/**
 * Extract headers from an Excel sheet
 */
export const extractHeadersFromSheet = (
  sheet: WorkBook["Sheets"][string],
): string[] => {
  const headers: string[] = [];
  const headerSet = new Set<string>();
  const duplicates = new Set<string>();

  if (!sheet["!ref"] || !sheet["!data"]) return headers;

  const range = utils.decode_range(sheet["!ref"]);
  const headerRowIndex = range.s.r; // First row as header
  const headerRow = sheet["!data"][headerRowIndex];

  // Iterate through all columns in the first row
  for (let c = range.s.c; c <= range.e.c; c++) {
    const cell = headerRow[c];

    if (cell && cell.v !== undefined && cell.v !== null) {
      const headerText = String(cell.v).trim();
      headers.push(headerText);

      // Track duplicates
      if (headerSet.has(headerText)) {
        duplicates.add(headerText);
      } else {
        headerSet.add(headerText);
      }
    }
  }

  // Log any duplicates found
  if (duplicates.size > 0) {
    console.warn(
      `Duplicate headers found: ${Array.from(duplicates).join(", ")}. Following left-to-right matching convention.`,
    );
  }

  return headers;
};
export type TMapper = { index: number; key: string };

export type TPlaceholderMapper<DefVal = unknown> = {
  key: string;
  defaultValue: DefVal;
};

export type TMixedMapper<DefVal = unknown> =
  | TMapper
  | TPlaceholderMapper<DefVal>;

type TMixedMappingToRecord<
  M extends readonly TMixedMapper[],
  TArrayData extends readonly unknown[],
> = {
  [K in M[number] as K["key"]]: K extends TMapper
    ? TArrayData[K["index"]]
    : K extends TPlaceholderMapper<infer U>
      ? U
      : never;
};

const isMapperType = (record: Record<string, unknown>): record is TMapper => {
  return "index" in record && "key" in record;
};
const isPlaceholderMapperType = <DefVal = unknown>(
  record: Record<string, unknown>,
): record is TPlaceholderMapper<DefVal> => {
  return "key" in record && "defaultValue" in record;
};
/**
 * Factory function that creates a mapper function to mappers array elements to object properties based on the provided mappers.
 * @param mappers
 * @example
 * const data = [30, 'John', 'Doe', 'Extra'];
 * const mappers = [
 * { index: 0, key: 'firstName' },
 * { index: 1, key: 'lastName' },
 * { index: 2, key: 'age' }
 * { key: 'country', defaultValue: 'USA' } // Placeholder with default value
 * ];
 * const mapper = arrayMapper(mappers);
 * const result = mapper(data);
 * // result is { firstName: 'John', lastName: 'Doe', age: 30, country: 'USA' }
 */
export const arrayMapper =
  <TArrayData extends readonly unknown[], M extends readonly TMixedMapper[]>(
    mappers: M,
  ): ((arr: TArrayData) => TMixedMappingToRecord<M, TArrayData>) =>
  (arr: TArrayData) =>
    Object.fromEntries(
      mappers.map((mapper) => {
        if (isMapperType(mapper)) {
          return [mapper.key, arr[mapper.index]] as const;
        } else if (isPlaceholderMapperType(mapper)) {
          return [mapper.key, mapper.defaultValue] as const;
        }
        invariant(false, "Invalid mapper type");
      }),
    ) as TMixedMappingToRecord<M, TArrayData>;

type TNotNullish<T> = Exclude<T, null | undefined>;

/**
 * Factory function that creates a type guard to check for required fields in an object.
 * @param keys
 * @example
 * const hasNameAndAge = objectFieldChecker(['name', 'age']);
 * const objArray = [{ name: 'John', age: 30 }, { name: 'Jane' }, { age: 25 }, { name: null, age: 40 }];
 * const filtered = objArray.filter(hasNameAndAge);
 *
 *
 */

export const objectFieldChecker =
  <K extends readonly PropertyKey[]>(keys: K) =>
  <T extends Record<PropertyKey, unknown>>(
    obj: T,
  ): obj is T & { [P in K[number]]: TNotNullish<T[P]> } => {
    if (obj === null || typeof obj !== "object") return false;
    for (const k of keys) {
      // Must have the property (own or via prototype) and be non-nullish.
      if (!(k in obj)) return false;
      const v = (obj as Record<PropertyKey, unknown>)[k];
      if (v === null || v === undefined) return false;
    }
    return true;
  };
