import type { ParsingOptions, WorkBook } from "xlsx";
import { read } from "xlsx";
import { z } from "zod";

import {
  TColumnSchema,
  TResolvedColumn,
  TUnresolvedColumn,
} from "~/domain/ColumnResolver";
import {
  columnSchemaFactory,
  TColumnRegistryName,
} from "~/domain/resolvers/columnRegistry";
import {
  extractDataFromResolved,
  resolveColumns,
} from "~/hooks/upload/useExcelReader/columnResolver/columnResolve";
import { TValidation } from "~/hooks/upload/useExcelReader/columnSheetReaderTypes";
import invariant from "~/utils/invariant";

type TResolvedColumnsResult = {
  fileName: string;
  sheetName: string;
  resolvedColumns: TResolvedColumn[];
  unresolvedColumns: TUnresolvedColumn[];
};

type TResolvedDataResult = {
  fileName: string;
  sheetName: string;
  resolvedColumns: TResolvedColumn[];
  unresolvedColumns: TUnresolvedColumn[];
  resolvedData: Record<string, unknown>[];
};

interface IColumnResolutionResult {
  data: unknown[];
  fileName: string;
  sheetName: string;
  getData: (fileName: string, sheetName: string) => Record<string, unknown>[];
  isValid: (fileName: string, sheetName: string) => boolean;
}

/** Data that the user has reviewed. Potentially modified from workbook data */
interface IColumnReviewedResult {
  validatedRows: Record<string, unknown>[];
  errors: { row: number; issues: string[] }[];
  errorTypes: Map<string, number>;
  fileName: string;
  sheetName: string;
  registryName: TColumnRegistryName;
  isValid: (
    fileName: string,
    sheetName: string,
    registryName: TColumnRegistryName,
  ) => boolean;
}

class ColumnResolutionResult implements IColumnResolutionResult {
  data: Record<string, unknown>[];
  fileName: string;
  sheetName: string;

  constructor(
    data: Record<string, unknown>[],
    fileName: string,
    sheetName: string,
  ) {
    this.data = data;
    this.fileName = fileName;
    this.sheetName = sheetName;
  }

  getData(fileName: string, sheetName: string) {
    invariant(this.fileName === fileName, "File name does not match.");
    invariant(this.sheetName === sheetName, "Sheet name does not match.");
    return this.data;
  }

  isValid(fileName: string, sheetName: string) {
    return this.fileName === fileName && this.sheetName === sheetName;
  }
}

class ColumnReviewedData implements IColumnReviewedResult {
  validatedRows: Record<string, unknown>[];
  errors: { row: number; issues: string[] }[];
  errorTypes: Map<string, number>;
  fileName: string;
  sheetName: string;
  registryName: TColumnRegistryName;

  constructor(
    fileName: string,
    sheetName: string,
    registryName: TColumnRegistryName,
    validatedRows: Record<string, unknown>[],
    errors: { row: number; issues: string[] }[],
    errorTypes: Map<string, number>,
  ) {
    this.validatedRows = validatedRows;
    this.errors = errors;
    this.errorTypes = errorTypes;
    this.fileName = fileName;
    this.sheetName = sheetName;
    this.registryName = registryName;
  }

  isValid(
    fileName: string,
    sheetName: string,
    registryName: TColumnRegistryName,
  ) {
    return (
      this.fileName === fileName &&
      this.sheetName === sheetName &&
      this.registryName === registryName
    );
  }
}

interface IColumnSheetReaderState {
  workbook_: WorkBook | null;
  workbook: WorkBook;
  fileName_: string | null;
  fileName: string;
  registryName_: TColumnRegistryName | null;
  registryName: TColumnRegistryName;
  reviewedData: IColumnReviewedResult | null;
  getValidatedData: (
    fileName: string,
    sheetName: string,
  ) => TValidation & { fileName: string; sheetName: string };

  resolutionResult: IColumnResolutionResult | null;
  reset: () => void;
  loadWorkbook: (file: File, options: ParsingOptions) => Promise<string>;
  getWorkbookSheets: (fileName: string) => {
    sheetNames: string[];
    fileName: string;
  };
  getResolvedColumns: (
    fileName: string,
    sheetName: string,
    columnsSchema: TColumnSchema[],
  ) => TResolvedColumnsResult;
  getSheet: (sheetName: string) => WorkBook["Sheets"][string];
  getResolvedData: (
    fileName: string,
    sheetName: string,
    schema: TColumnSchema[],
  ) => TResolvedDataResult;
  clearResolvedData: () => void;
  validateReviewedData: (
    fileName: string,
    sheetName: string,
    registryName: TColumnRegistryName,
    reviewedData: Record<string, unknown>[],
    start: number,
    end: number,
  ) => Promise<{
    fileName: string;
    sheetName: string;
    registryName: TColumnRegistryName;
  }>;
}

export class ColumnSheetReaderState implements IColumnSheetReaderState {
  workbook_: WorkBook | null = null;
  fileName_: string | null = null;
  registryName_: TColumnRegistryName | null = null;
  resolutionResult: IColumnResolutionResult | null = null;
  reviewedData: IColumnReviewedResult | null = null;

  reset() {
    this.workbook_ = null;
    this.fileName_ = null;
    this.resolutionResult = null;
    this.registryName_ = null;
    this.reviewedData = null;
  }

  get workbook() {
    invariant(this.workbook_, "Workbook not loaded. Call loadWorkbook first.");
    return this.workbook_;
  }

  get fileName() {
    invariant(this.fileName_, "File name not set. Call loadWorkbook first.");
    return this.fileName_;
  }

  get registryName() {
    invariant(
      this.registryName_,
      "Registry name not set. Call validateReviewedData first.",
    );
    return this.registryName_;
  }
  getSheet(sheetName: string) {
    const sheets = this.workbook.Sheets;
    const sheet = sheets[sheetName];
    invariant(sheet, `Sheet "${sheetName}" not found in the workbook.`);
    return sheet;
  }

  async loadWorkbook(file: File, options: ParsingOptions): Promise<string> {
    this.reset();

    try {
      this.fileName_ = file.name;
      const buffer = await file.arrayBuffer();
      this.workbook_ = read(buffer, options);
      return this.fileName_;
    } catch (error) {
      this.reset();
      console.error("Error loading workbook:", error);
      throw error;
    }
  }

  getWorkbookSheets(fileName: string) {
    if (this.fileName !== fileName) {
      throw new Error("File name does not match the loaded workbook.");
    }
    return {
      fileName: this.fileName,
      sheetNames: this.workbook.SheetNames,
    };
  }

  getResolvedColumns(
    fileName: string,
    sheetName: string,
    columnsSchema: TColumnSchema[],
  ) {
    if (this.fileName !== fileName) {
      throw new Error("File name does not match the loaded workbook.");
    }
    const sheet = this.workbook.Sheets[sheetName];
    const { resolvedColumns, unresolvedColumns } = resolveColumns(
      sheet,
      columnsSchema,
    );
    return {
      fileName: this.fileName,
      sheetName,
      resolvedColumns,
      unresolvedColumns,
    };
  }

  /** Look ahead, return reviewed data, if present, otherwise read from WorkSheet **/
  getResolvedData(
    fileName: string,
    sheetName: string,
    schema: TColumnSchema[],
  ) {
    const sheet = this.getSheet(sheetName);
    const { resolvedColumns, unresolvedColumns } = resolveColumns(
      sheet,
      schema,
    );
    const previousResult = this.resolutionResult;
    if (previousResult && previousResult.isValid(fileName, sheetName)) {
      return {
        resolvedData: previousResult.getData(fileName, sheetName),
        resolvedColumns,
        unresolvedColumns,
        fileName,
        sheetName,
      };
    } else if (previousResult && !previousResult.isValid(fileName, sheetName)) {
      this.resolutionResult = null;
    }
    const resolvedData = extractDataFromResolved(sheet, resolvedColumns);
    this.resolutionResult = new ColumnResolutionResult(
      resolvedData,
      fileName,
      sheetName,
    );
    this.reviewedData = null;
    return {
      resolvedData,
      resolvedColumns,
      unresolvedColumns,
      fileName,
      sheetName,
    };
  }

  clearResolvedData() {
    this.resolutionResult = null;
    this.reviewedData = null;
  }

  async validateReviewedData(
    fileName: string,
    sheetName: string,
    registryName: TColumnRegistryName,
    reviewedData: Record<string, unknown>[],
    start: number,
    end: number,
  ) {
    this.registryName_ = registryName;
    this.reviewedData = null;
    const headers = Object.keys(reviewedData[0]);
    const registry = columnSchemaFactory.getColumnResolver(this.registryName);
    let schema: z.ZodObject<Record<string, z.ZodType<unknown>>>;
    try {
      schema = registry.buildObjectSchema(headers);
    } catch (error) {
      console.error("Error building schema:", error);
      throw new Error("Failed to build schema from registry.");
    }
    const valids: z.infer<typeof schema>[] = [];
    const errors: { row: number; issues: string[] }[] = [];
    const errorTypes = new Map<string, number>();
    for (let i = start; i < end; i++) {
      const row = reviewedData[i];
      const result = schema.safeParse(row);
      if (!result.success) {
        const zodError = result.error;
        zodError.issues.forEach((issue) => {
          const key = issue.message;
          errorTypes.set(key, (errorTypes.get(key) || 0) + 1);
        });
        const issues = result.error.errors.map((err) =>
          err.path.length > 0
            ? `${err.path.join(".")}: ${err.message}`
            : err.message,
        );
        errors.push({ row: i + 1, issues });
      } else {
        valids.push(result.data);
      }
    }
    this.reviewedData = new ColumnReviewedData(
      fileName,
      sheetName,
      registryName,
      valids,
      errors,
      errorTypes,
    );
    return { fileName, sheetName, registryName };
  }

  getValidatedData(fileName: string, sheetName: string) {
    invariant(this.reviewedData, "No reviewed data available.");
    if (!this.reviewedData.isValid(fileName, sheetName, this.registryName)) {
      throw new Error("Reviewed data does not match the requested file/sheet.");
    }
    const { validatedRows, errors, errorTypes } = this.reviewedData;
    return { fileName, sheetName, validatedRows, errors, errorTypes };
  }
}
