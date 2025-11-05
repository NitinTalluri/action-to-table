import { z } from "zod";

import { TDateFormatEnum } from "~/domain/grids/Cell";
import { generateDateValidationSchema } from "~/utils/dates";

type TPrimitive = string | number | null | undefined;
export type TPrimitiveRecord = Record<string, TPrimitive>;
type TSuccessParse<T> = {
  success: true; // Overall success
  data: T;
};
type TParseIssue = {
  row: number;
  column: string;
  message: string;
};
type TErrorParse = {
  success: false; // Overall failure
  errors: TParseIssue[];
};
type TParseResponse<T> = TSuccessParse<T> | TErrorParse;
type TColumnDef<ColNames extends string = string> = {
  title: string;
  field: ColNames;
  source: ColNames;
  align?: "left" | "center" | "right";
  width?: number;
  _hide?: boolean;
};
type TFlatError = {
  rowIndex: number;
  row: Record<string, string>;
};

export interface IGridDataProcessor<Schema extends z.ZodTypeAny> {
  columns: TColumnDef[];
  schema: Schema;
  parseRows: (
    rows: TPrimitiveRecord[],
    dateCols?: string[],
    dateFormat?: TDateFormatEnum,
  ) => TParseResponse<z.infer<Schema>>;
  createEmptyRows: (count: number) => Record<string, string>[];
  formatErrors: (errors: TParseIssue[]) => TFlatError[];
}

export class GridDataProcessor<Schema extends z.ZodTypeAny>

/**
 * @param columns - The columns of the grid
 * @param schema - The schema to validate the rows against. This schema should be an array schema with object items.
 */
  implements IGridDataProcessor<Schema>
{
  columns: TColumnDef[];
  schema: Schema;
  private emptyRowTemplate: Record<string, string>;

  constructor(columns: TColumnDef[], schema: Schema) {
    this.columns = columns;
    this.schema = schema;
    this.emptyRowTemplate = this.createEmptyRowTemplate();
  }

  isNotEmptyRow = (row: Record<string, unknown>) => {
    // Don't use rows that have no data
    const isNotEmpty = (value: unknown) =>
      value !== null && value !== undefined && value !== "";

    return Object.values(row).some(isNotEmpty);
  };

  filterRow = (
    row: Record<string, unknown> | undefined | null,
  ): row is TPrimitiveRecord => {
    // Has some data
    return !!row && this.isNotEmptyRow(row);
  };

  filterRows = (rows: (TPrimitiveRecord | undefined | null)[]) => {
    const rowIndices: number[] = [];
    const filteredRows = rows
      .map((row, index) => {
        if (this.filterRow(row)) {
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

  extractErrors = (errors: z.ZodIssue[]) => {
    // Ensure that the error is a row error (i.e. has a path of length 2)
    // and that the first path is a number (row index) and the second path is a string (column name)
    const rowErrors = errors.filter(
      (error) =>
        error.path.length === 2 &&
        typeof error.path[0] === "number" &&
        typeof error.path[1] === "string",
    );
    // Errors may be superRefined (i.e. the columns are valid but together they are invalid)
    const columnErrors = errors
      .filter(
        (error) => error.path.length === 1 && typeof error.path[0] === "number",
      )
      .map((error) => {
        return {
          ...error,
          path: [error.path[0], "Issue"],
        };
      });
    return [...rowErrors, ...columnErrors] as z.ZodIssue[];
  };

  parseRows = (
    rows: TPrimitiveRecord[],
    dateCols?: string[],
    dateFormat?: TDateFormatEnum,
  ): TParseResponse<z.infer<Schema>> => {
    const { filteredRows, rowIndices } = this.filterRows(rows);
    let dateErrors: TParseIssue[] = [];

    if (dateCols && dateCols.length) {
      const dateValidationSchema = generateDateValidationSchema(
        dateCols,
        dateFormat,
      );

      const dateParsedRows = dateValidationSchema.safeParse(filteredRows);

      if (!dateParsedRows.success) {
        dateErrors = this.extractErrors(dateParsedRows.error.errors).map(
          (error) => {
            const path = error.path;
            const arrayIdx = path[0] as number;
            const sheetIdx = rowIndices[arrayIdx] ?? arrayIdx;
            return {
              row: sheetIdx,
              column:
                this.columns.find((c) => c.field === path[1])?.title ||
                (path[1] as string),
              message: error.message,
            };
          },
        );
      }
    }

    const parsedRows = this.schema.safeParse(filteredRows);
    if (parsedRows.success && dateErrors.length === 0) {
      return {
        success: true,
        data: parsedRows.data as z.infer<Schema>,
      };
    }

    const errors = parsedRows.success
      ? []
      : this.extractErrors(parsedRows.error.errors).map((error) => {
          const path = error.path;
          const arrayIdx = path[0] as number;
          const sheetIdx = rowIndices[arrayIdx] ?? arrayIdx;

          return {
            row: sheetIdx,
            column:
              this.columns.find((c) => c.field === path[1])?.title ||
              (path[1] as string),
            message: error.message,
          };
        });

    return {
      success: false,
      errors: errors.concat(dateErrors),
    };
  };

  createEmptyRowTemplate = () => {
    return this.columns.reduce((acc, column) => {
      return {
        ...acc,
        [column.field]: "",
      };
    }, {});
  };

  createEmptyRow = () => {
    return { ...this.emptyRowTemplate };
  };

  createEmptyRows = (n: number) =>
    Array.from({ length: n }, this.createEmptyRow);

  formatErrors = (errors: TParseIssue[]) => {
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
}
