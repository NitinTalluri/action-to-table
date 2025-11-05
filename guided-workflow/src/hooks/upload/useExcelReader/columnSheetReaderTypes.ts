import { ParsingOptions } from "xlsx";

import {
  TColumnSchema,
  TResolvedColumn,
  TUnresolvedColumn,
} from "~/domain/ColumnResolver";
import { TColumnRegistryName } from "~/domain/resolvers/columnRegistry";
// reference this file src/hooks/upload/useExcelReader/sheetReaderTypes.ts

type TClient = "client";
type TWorker = "worker";

type TReq = {
  reqId: string;
};

export type TValidation = {
  validatedRows: Record<string, unknown>[];
  errors: { row: number; issues: string[] }[];
  errorTypes: Map<string, number>;
};

type TLoadWorkbookMessage = TReq & {
  type: "loadWorkbook";
  sender: TClient;
  payload: File;
  options: Exclude<ParsingOptions, "type">;
};
type TLoadWorkbookReply = TReq & {
  type: "loadWorkbook";
  sender: TWorker;
  payload: { fileName: string };
};

type TGetSheetsMessage = TReq & {
  type: "getSheets";
  sender: TClient;
  payload: { fileName: string };
};

type TGetSheetsReply = TReq & {
  type: "getSheets";
  sender: TWorker;
  payload: { sheetNames: string[]; fileName: string };
};

type TGetResolvedColumnsMessage = TReq & {
  type: "getResolvedColumns";
  sender: TClient;
  payload: { fileName: string; sheetName: string; schema: TColumnSchema[] };
};

type TGetResolvedColumnsReply = TReq & {
  type: "getResolvedColumns";
  sender: TWorker;
  payload: {
    fileName: string;
    sheetName: string;
    resolvedColumns: TResolvedColumn[];
    unresolvedColumns: TUnresolvedColumn[];
  };
};

type TGetResolvedDataMessage = TReq & {
  type: "getResolvedData";
  sender: TClient;
  payload: { fileName: string; sheetName: string; schema: TColumnSchema[] };
};

type TGetResolvedDataReply = TReq & {
  type: "getResolvedData";
  sender: TWorker;
  payload: {
    fileName: string;
    sheetName: string;
    resolvedColumns: TResolvedColumn[];
    unresolvedColumns: TUnresolvedColumn[];
    resolvedData: Record<string, unknown>[];
  };
};

type TClearResolvedDataMessage = TReq & {
  type: "clearResolvedData";
  sender: TClient;
  payload: null;
};

type TClearResolvedDataReply = TReq & {
  type: "clearResolvedData";
  sender: TWorker;
  payload: null;
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
  type: "validateData";
  sender: TClient;
  payload: {
    fileName: string;
    sheetName: string;
    registryName: TColumnRegistryName;
    reviewedData: Record<string, unknown>[];
  };
};

type TValidateReply = TReq & {
  type: "validateData";
  sender: TWorker;
  payload: {
    fileName: string;
    sheetName: string;
  };
};

type TGetValidatedDataMessage = TReq & {
  type: "getValidatedData";
  sender: TClient;
  payload: {
    fileName: string;
    sheetName: string;
  };
};

type TGetValidatedDataReply = TReq & {
  type: "getValidatedData";
  sender: TWorker;
  payload: {
    fileName: string;
    sheetName: string;
  } & TValidation;
};

export type ToColumnWorkerMessage =
  | TLoadWorkbookMessage
  | TGetSheetsMessage
  | TGetResolvedColumnsMessage
  | TGetResolvedDataMessage
  | TClearResolvedDataMessage
  | TValidateMessage
  | TGetValidatedDataMessage
  | TResetMessage;

export type FromColumnWorkerMessage =
  | TLoadWorkbookReply
  | TGetSheetsReply
  | TGetResolvedColumnsReply
  | TGetResolvedDataReply
  | TClearResolvedDataReply
  | TValidateReply
  | TGetValidatedDataReply
  | TResetReply;

export type TypedColumnWorker<
  In = ToColumnWorkerMessage,
  Out = FromColumnWorkerMessage,
> = Omit<Worker, "postMessage" | "onmessage"> & {
  postMessage: (message: Out, transfer?: Transferable[]) => void;
  onmessage: ((ev: MessageEvent<In>) => void) | null;
  location: WorkerLocation;
};
