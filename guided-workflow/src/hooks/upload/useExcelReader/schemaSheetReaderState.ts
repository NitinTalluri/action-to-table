import type { ParsingOptions, WorkBook } from "xlsx";
import { read } from "xlsx";
import { z } from "zod";

import {
  ISchemaInferenceResult,
  schemaRegistry,
  TSchemaInferenceName,
  TSchemaInferenceNamespace,
} from "~/domain/resolvers/schemaInferenceRegistry";
import {
  getResolvedDataFromInference,
  inferSchema,
} from "~/hooks/upload/useExcelReader/schemaResolver/schemaResolve";
import { TSuccessfulSchemaInferenceResult } from "~/hooks/upload/useExcelReader/schemaSheetReaderTypes";
import invariant from "~/utils/invariant";

type TGenericData = Record<string, unknown>;

type TValidation = {
  validatedRows: TGenericData[];
  errors: { row: number; issues: string[] }[];
  errorTypes: Map<string, number>;
};

const isSuccessfulInference = <N extends TSchemaInferenceNamespace>(
  result: ISchemaInferenceResult,
): result is TSuccessfulSchemaInferenceResult<N> => {
  return (
    result.isCompatible &&
    result.schemaName !== null &&
    !("errorMessage" in result)
  );
};

interface ISchemaSheetReaderState<N extends TSchemaInferenceNamespace> {
  workbook_: WorkBook | null;
  workbook: WorkBook;
  fileName_: string | null;

  namespace_: N | null;
  sheetName_: string | null;

  /** Dependent values */
  namespace: N;
  fileName: string;
  sheetName: string;
  currentSheet: WorkBook["Sheets"][string];
  resolutionResult: TSuccessfulSchemaInferenceResult<N> | null;
  resolutionDroppedRowCount: number;
  resolvedData: TGenericData[] | null;
  reviewedData: TGenericData[] | null;
  validatedData: TValidation | null;

  loadWorkbook: (
    file: File,
    options: ParsingOptions,
    namespace: N,
  ) => Promise<string>;
  getSheets: (fileName: string) => { fileName: string; sheetNames: string[] };

  inferSchema: (
    fileName: string,
    sheetName: string,
  ) => Promise<ISchemaInferenceResult<N>>;

  validateData: (
    fileName: string,
    sheetName: string,
    reviewedData: TGenericData[],
    start: number,
    end: number,
  ) => Promise<void>;

  getResolvedData: (
    fileName: string,
    sheetName: string,
  ) => Promise<{
    resolvedData: TGenericData[];
    droppedRowCount: number;
    fileName: string;
    sheetName: string;
  }>;

  resetResolvedData: () => void;
  getValidatedData: (fileName: string, sheetName: string) => TValidation;
  resetValidatedData: () => void;

  reset: () => void;
}

export class SchemaSheetReaderState<N extends TSchemaInferenceNamespace>
  implements ISchemaSheetReaderState<N>
{
  workbook_: WorkBook | null = null;
  fileName_: string | null = null;
  sheetName_: string | null = null;
  namespace_: N | null = null;

  resolutionResult_: TSuccessfulSchemaInferenceResult<N> | null = null;
  resolvedData_: TGenericData[] | null = null;
  reviewedData_: TGenericData[] | null = null;
  validatedData_: TValidation | null = null;
  resolutionDroppedRowCount: number = 0;

  reset = () => {
    this.workbook_ = null;
    this.fileName_ = null;
    this.sheetName_ = null;
    this.namespace_ = null;
    this.resolutionResult = null;
    this.reviewedData = null;
  };

  get workbook(): WorkBook {
    invariant(this.workbook_, "Workbook not loaded");
    return this.workbook_;
  }

  get namespace(): N {
    invariant(this.namespace_, "Namespace not set");
    return this.namespace_;
  }

  set namespace(value: N) {
    this.namespace_ = value;
    this.fileName_ = null;
    this.sheetName_ = null;
    this.resolutionResult = null;
    this.resolvedData = null;
    this.reviewedData = null;
    this.validatedData = null;
  }

  get fileName(): string {
    invariant(this.fileName_, "File name not set");
    return this.fileName_;
  }

  set fileName(value: string) {
    this.fileName_ = value;
    this.sheetName_ = null;
    this.resolutionResult = null;
    this.resolvedData = null;
    this.reviewedData = null;
    this.validatedData = null;
  }

  get sheetName(): string {
    invariant(this.sheetName_, "Sheet name not set");
    return this.sheetName_;
  }

  set sheetName(value: string) {
    this.sheetName_ = value;
    this.resolutionResult = null;
    this.resolvedData = null;
    this.reviewedData = null;
    this.validatedData = null;
  }

  get resolutionResult() {
    return this.resolutionResult_;
  }

  set resolutionResult(value) {
    if (value && !isSuccessfulInference(value)) {
      throw new Error(
        "Only successful inference results can be set as resolutionResult",
      );
    }
    this.resolutionResult_ = value;
    this.resolvedData_ = null;
    this.reviewedData_ = null;
    this.validatedData_ = null;
  }

  get resolvedData() {
    return this.resolvedData_;
  }

  set resolvedData(value: TGenericData[] | null) {
    this.resolvedData_ = value;
    if (this.resolvedData_ === null) {
      this.resolutionDroppedRowCount = 0;
    }
    this.reviewedData_ = null;
    this.validatedData_ = null;
  }

  get reviewedData() {
    return this.reviewedData_;
  }

  set reviewedData(value: TGenericData[] | null) {
    this.reviewedData_ = value;
    this.validatedData_ = null;
  }

  get validatedData() {
    return this.validatedData_;
  }

  set validatedData(value: TValidation | null) {
    this.validatedData_ = value;
  }

  get currentSheet() {
    const sheet = this.workbook.Sheets[this.sheetName];
    invariant(sheet, `Sheet "${this.sheetName}" not found in the workbook.`);
    return sheet;
  }

  async loadWorkbook(file: File, options: ParsingOptions, namespace: N) {
    this.fileName_ = file.name;

    try {
      this.namespace_ = namespace;
      this.fileName_ = file.name;
      const arrayBuffer = await file.arrayBuffer();
      this.workbook_ = read(arrayBuffer, options);
    } catch (error) {
      this.reset();
      console.error("Error loading workbook:", error);
      throw error;
    }
    return this.fileName;
  }

  getSheets(fileName: string) {
    if (fileName !== this.fileName) {
      throw new Error("File name does not match loaded workbook");
    }
    return {
      fileName: this.fileName,
      sheetNames: this.workbook.SheetNames,
    };
  }

  async inferSchema(fileName: string, sheetName: string) {
    if (fileName !== this.fileName) {
      throw new Error("File name does not match loaded workbook");
    }
    this.sheetName = sheetName;
    const sheet = this.currentSheet;
    const namespace = this.namespace;
    const inferenceResult = await inferSchema(sheet, namespace);

    if (
      isSuccessfulInference<typeof namespace>(inferenceResult) &&
      inferenceResult.isCompatible
    ) {
      this.resolutionResult = inferenceResult;
    }

    return inferenceResult;
  }

  async getResolvedData(fileName: string, sheetName: string) {
    if (fileName !== this.fileName) {
      throw new Error("File name does not match loaded workbook");
    }
    if (sheetName !== this.sheetName) {
      throw new Error("Sheet name does not match selected sheet");
    }
    if (!this.resolutionResult?.isCompatible) {
      throw new Error("Schema not resolved or incompatible");
    }

    // If we have user-reviewed data, return that first before falling back to data retrieved from worksheet
    const previous = this.reviewedData || this.resolvedData;
    if (previous) {
      return {
        resolvedData: previous,
        droppedRowCount: this.resolutionDroppedRowCount,
        fileName: this.fileName,
        sheetName: this.sheetName,
      };
    }

    const inferenceResult = this.resolutionResult;

    const sheet = this.currentSheet;
    const { rows, droppedRowCount } = getResolvedDataFromInference(
      sheet,
      inferenceResult,
    );
    this.resolvedData = rows;
    this.resolutionDroppedRowCount = droppedRowCount;
    return {
      resolvedData: rows,
      droppedRowCount,
      fileName: this.fileName,
      sheetName: this.sheetName,
    };
  }

  resetResolvedData() {
    this.resolvedData = null;
  }

  /** After user has reviewed the resolved data, we'll attempt to validate against an external zod schema. We'll track this data as reviewed */
  async validateData(
    fileName: string,
    sheetName: string,
    reviewedData: TGenericData[],
    start: number,
    end: number,
  ) {
    if (fileName !== this.fileName) {
      throw new Error("File name does not match loaded workbook");
    }
    if (sheetName !== this.sheetName) {
      throw new Error("Sheet name does not match selected sheet");
    }
    const inferenceResult = this.resolutionResult;

    // Intentionally setting both resolvedData and reviewedData to the same value
    this.resolvedData = reviewedData;
    this.reviewedData = reviewedData;

    invariant(
      inferenceResult,
      "Schema must be resolved before validating data",
    );
    const namespace = this.namespace;
    const inferredSchemaName =
      inferenceResult.schemaName as TSchemaInferenceName<typeof namespace>;
    console.log("Validating data against schema", { inferredSchemaName });
    const externalSchema = schemaRegistry.getExternalSchemaInNamespace(
      inferredSchemaName,
      namespace,
    );
    const valids: z.infer<typeof externalSchema>[] = [];
    const errors: { row: number; issues: string[] }[] = [];
    const errorTypes = new Map<string, number>();
    for (let i = start; i < end; i++) {
      const row = reviewedData[i];
      const result = externalSchema.safeParse(row);
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

    this.validatedData = {
      validatedRows: valids,
      errors,
      errorTypes,
    };
  }

  getValidatedData(fileName: string, sheetName: string) {
    if (fileName !== this.fileName) {
      throw new Error("File name does not match loaded workbook");
    }
    if (sheetName !== this.sheetName) {
      throw new Error("Sheet name does not match selected sheet");
    }
    invariant(this.validatedData, "Data has not been validated yet");
    return this.validatedData;
  }

  resetValidatedData() {
    this.validatedData = null;
    this.resolvedData = null;
  }
}
