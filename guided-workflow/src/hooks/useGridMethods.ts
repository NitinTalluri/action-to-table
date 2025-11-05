import { z } from "zod";

type TPrimitive = string | number | null | undefined;
type TPrimitiveRecord = Record<string, TPrimitive>;
type TSuccessParse<T> = {
  success: true; // Overall success
  data: T;
};
export type TParseIssue = {
  row: number;
  column: string;
  message: string;
};
type TErrorParse = {
  success: false; // Overall failure
  errors: TParseIssue[];
};
type TParseResponse<T> = TSuccessParse<T> | TErrorParse;
export type TColumnDef<ColNames extends string = string> = {
  title: string;
  field: ColNames;
  source: ColNames;
  align?: "left" | "center" | "right";
  width?: number;
  _hide?: boolean;
};
export type TFlatError = {
  rowIndex: number;
  row: Record<string, string>;
};

const useGridMethods = <Schema extends z.ZodTypeAny>(
  columns: TColumnDef[],
  schema: Schema,
) => {
  type TOutput = z.infer<Schema>;
  const isNotEmptyRow = (row: Record<string, unknown>) => {
    // Don't use rows that have no data
    const isNotEmpty = (value: unknown) =>
      value !== null && value !== undefined && value !== "";

    return Object.values(row).some(isNotEmpty);
  };

  const filterRow = (
    row: Record<string, unknown> | undefined | null,
  ): row is TPrimitiveRecord => {
    // Has some data
    return !!row && isNotEmptyRow(row);
  };

  const filterRows = (rows: (TPrimitiveRecord | undefined | null)[]) => {
    const rowIndices: number[] = [];
    const filteredRows = rows
      .map((row, index) => {
        if (filterRow(row)) {
          rowIndices.push(index);
          return row;
        } else {
          return null;
        }
      })
      .filter((row): row is TPrimitiveRecord => {
        return !!row;
      });
    return {
      rowIndices,
      filteredRows,
    };
  };

  const createEmptyRow = () => {
    return columns.reduce((acc, column) => {
      return {
        ...acc,
        [column.field]: "",
      };
    }, {});
  };

  const createEmptyRows = (n: number) =>
    Array.from({ length: n }, createEmptyRow);

  const extractErrors = (errors: z.ZodIssue[]) => {
    // Ensure that the error is a row error (i.e. has a path of length 2)
    // and that the first path is a number (row index) and the second path is a string (column name)
    const rowErrors = errors.filter(
      (error) =>
        error.path.length === 2 &&
        typeof error.path[0] === "number" &&
        typeof error.path[1] === "string",
    );
    return rowErrors;
  };

  const parseRows = (rows: TPrimitiveRecord[]): TParseResponse<TOutput> => {
    const { filteredRows, rowIndices } = filterRows(rows);
    const parsedRows = schema.safeParse(filteredRows);
    if (parsedRows.success) {
      return {
        success: true,
        data: parsedRows.data as TOutput,
      };
    }

    const errors = extractErrors(parsedRows.error.errors).map((error) => {
      const path = error.path;
      const arrayIdx = path[0] as number;
      const sheetIdx = rowIndices[arrayIdx] ?? arrayIdx;
      return {
        row: sheetIdx,
        column: path[1] as string,
        message: error.message,
      };
    });

    return {
      success: false,
      errors,
    };
  };

  const formatErrors = (errors: TParseIssue[]) => {
    const columnsMentioned = new Set<string>(
      errors.map((error) => error.column),
    );

    const objMapEntries = Array.from(columnsMentioned).map((column) => {
      return [column, ""];
    });

    const rowFactory = () => {
      return Object.fromEntries(objMapEntries);
    };

    const rowErrors = new Map<number, Record<string, string>>();

    for (const error of errors) {
      const row = rowErrors.get(error.row) ?? rowFactory();
      row[error.column] = error.message;
      rowErrors.set(error.row, row);
    }

    const rowErrorsFlat = Array.from(rowErrors.entries()).map(
      ([rowIndex, row]) => {
        return { rowIndex, row };
      },
    );

    return rowErrorsFlat;
  };

  return {
    parseRows,
    createEmptyRow,
    createEmptyRows,
    formatErrors,
  };
};

export default useGridMethods;
