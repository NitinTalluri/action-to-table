import { ParsingOptions } from "xlsx";

import {
  ISchemaInferenceResult,
  TSchemaInferenceName,
  TSchemaInferenceNamespace,
} from "~/domain/resolvers/schemaInferenceRegistry";

type TClient = "client";
type TWorker = "worker";

type TReq = {
  reqId: string;
};
type TFileName = {
  fileName: string;
};
type TSheetName = {
  sheetName: string;
};
type TNameSpace = {
  namespace: TSchemaInferenceNamespace;
};
type TInfer = {
  inferenceResult: ISchemaInferenceResult;
};
type TResolve = {
  resolvedData: Record<string, unknown>[];
  droppedRowCount: number;
};
type TReviewed = {
  reviewedData: Record<string, unknown>[];
};

export type TValidation = {
  validatedRows: Record<string, unknown>[];
  errors: { row: number; issues: string[] }[];
  errorTypes: Map<string, number>;
};

type TSetNamespaceMessage = TReq & {
  type: "setNamespace";
  sender: TClient;
  payload: { namespace: TSchemaInferenceNamespace };
};

type TSetNamespaceReply = TReq & {
  type: "setNamespace";
  sender: TWorker;
  payload: { namespace: TSchemaInferenceNamespace };
};

type TLoadWorkbookMessage = TReq & {
  type: "loadWorkbook";
  sender: TClient;
  payload: File;
  options: Exclude<ParsingOptions, "type">;
};
type TLoadWorkbookMessageReply = TReq & {
  type: "loadWorkbook";
  sender: TWorker;
  payload: { fileName: string };
};

type TGetSheetsMessage = TReq & {
  type: "getSheets";
  sender: TClient;
  payload: TFileName;
};

type TGetSheetsReply = TReq & {
  type: "getSheets";
  sender: TWorker;
  payload: TFileName & { sheetNames: string[] };
};

type FSN = TFileName & TSheetName & TNameSpace;

type TInferSchemaMessage = TReq & {
  type: "inferSchema";
  sender: TClient;
  payload: FSN;
};

type TInferSchemaReply = TReq & {
  type: "inferSchema";
  sender: TWorker;
  payload: FSN & TInfer;
};

type TGetResolvedDataMessage = TReq & {
  type: "getResolvedData";
  sender: TClient;
  payload: FSN;
};

type TGetResolvedDataReply = TReq & {
  type: "getResolvedData";
  sender: TWorker;
  payload: FSN & TResolve;
};

type TResetMessage = TReq & {
  type: "reset";
  sender: TClient;
  payload: null;
};

type TResetReply = TReq & {
  type: "reset";
  sender: TWorker;
  payload: null;
};

type TValidateMessage = TReq & {
  type: "validate";
  sender: TClient;
  payload: FSN & TReviewed;
};

type TValidateReply = TReq & {
  type: "validate";
  sender: TWorker;
  payload: FSN;
};

type TGetValidatedDataMessage = TReq & {
  type: "getValidatedData";
  sender: TClient;
  payload: FSN;
};

type TGetValidatedDataReply = TReq & {
  type: "getValidatedData";
  sender: TWorker;
  payload: FSN & TValidation;
};

type TResetValidatedDataMessage = TReq & {
  type: "resetValidatedData";
  sender: TClient;
  payload: FSN;
};

type TResetValidatedDataReply = TReq & {
  type: "resetValidatedData";
  sender: TWorker;
  payload: FSN;
};

type TResetResolvedDataMessage = TReq & {
  type: "resetResolvedData";
  sender: TClient;
  payload: FSN;
};

type TResetResolvedDataReply = TReq & {
  type: "resetResolvedData";
  sender: TWorker;
  payload: FSN;
};

export type ToSchemaWorkerMessage =
  | TSetNamespaceMessage
  | TLoadWorkbookMessage
  | TGetSheetsMessage
  | TInferSchemaMessage
  | TGetResolvedDataMessage
  | TResetMessage
  | TValidateMessage
  | TGetValidatedDataMessage
  | TResetValidatedDataMessage
  | TResetResolvedDataMessage;

export type FromSchemaWorkerMessage =
  | TSetNamespaceReply
  | TLoadWorkbookMessageReply
  | TGetSheetsReply
  | TInferSchemaReply
  | TGetResolvedDataReply
  | TResetReply
  | TValidateReply
  | TGetValidatedDataReply
  | TResetValidatedDataReply
  | TResetResolvedDataReply;

export type TypedSchemaWorker<
  In = ToSchemaWorkerMessage,
  Out = FromSchemaWorkerMessage,
> = Omit<Worker, "postMessage" | "onmessage"> & {
  postMessage: (message: Out, transfer?: Transferable[]) => void;
  onmessage: ((ev: MessageEvent<In>) => void) | null;
  location: WorkerLocation;
};
/**
 * Represents a successful schema inference result with a valid schema
 * and compatibility guaranteed
 */
export type TSuccessfulSchemaInferenceResult<
  T extends TSchemaInferenceNamespace = TSchemaInferenceNamespace,
> = Omit<
  ISchemaInferenceResult<T>,
  "schemaName" | "isCompatible" | "errorMessage"
> & {
  // schemaName will always be present (not null)
  schemaName: TSchemaInferenceName<T>;
  // isCompatible will always be true
  isCompatible: true;
  // errorMessage will never be present for successful results
  errorMessage?: never;
};
