/// <reference lib="webworker" />
import { ColumnSheetReaderState } from "~/hooks/upload/useExcelReader/columnSheetReaderState";
import {
  ToColumnWorkerMessage,
  TypedColumnWorker,
} from "~/hooks/upload/useExcelReader/columnSheetReaderTypes";

type Ctx = TypedColumnWorker;

declare const self: Ctx;
const workerState = new ColumnSheetReaderState();

const handleMessage = async (event: MessageEvent<ToColumnWorkerMessage>) => {
  const msg = event.data;
  switch (msg.type) {
    case "loadWorkbook": {
      const { payload: file, options, reqId } = msg;
      const fileName = await workerState.loadWorkbook(file, options);
      self.postMessage({
        type: msg.type,
        sender: "worker",
        payload: { fileName },
        reqId,
      });
      break;
    }
    case "getSheets": {
      const {
        payload: { fileName },
        reqId,
      } = msg;
      const { sheetNames } = workerState.getWorkbookSheets(fileName);
      self.postMessage({
        type: msg.type,
        sender: "worker",
        payload: { fileName, sheetNames },
        reqId,
      });
      break;
    }
    case "getResolvedColumns": {
      const {
        payload: { fileName, sheetName, schema },
        reqId,
      } = msg;
      const { resolvedColumns, unresolvedColumns } =
        workerState.getResolvedColumns(fileName, sheetName, schema);
      self.postMessage({
        type: msg.type,
        sender: "worker",
        payload: { fileName, sheetName, resolvedColumns, unresolvedColumns },
        reqId,
      });
      break;
    }
    case "getResolvedData": {
      const {
        payload: { fileName, sheetName, schema },
        reqId,
      } = msg;
      const { resolvedColumns, unresolvedColumns, resolvedData } =
        workerState.getResolvedData(fileName, sheetName, schema);
      self.postMessage({
        type: msg.type,
        sender: "worker",
        payload: {
          fileName,
          sheetName,
          resolvedColumns,
          unresolvedColumns,
          resolvedData,
        },
        reqId,
      });
      break;
    }
    case "clearResolvedData": {
      const { reqId } = msg;
      workerState.clearResolvedData();
      self.postMessage({
        type: msg.type,
        sender: "worker",
        payload: null,
        reqId,
      });
      break;
    }
    case "validateData": {
      const {
        payload: { fileName, sheetName, registryName, reviewedData },
        reqId,
      } = msg;
      const result = await workerState.validateReviewedData(
        fileName,
        sheetName,
        registryName,
        reviewedData,
        0,
        reviewedData.length,
      );
      self.postMessage({
        type: msg.type,
        sender: "worker",
        payload: result,
        reqId,
      });
      break;
    }
    case "getValidatedData": {
      const {
        payload: { fileName, sheetName },
        reqId,
      } = msg;
      const { validatedRows, errors, errorTypes } =
        workerState.getValidatedData(fileName, sheetName);
      self.postMessage({
        type: msg.type,
        sender: "worker",
        payload: { fileName, sheetName, validatedRows, errors, errorTypes },
        reqId,
      });

      break;
    }

    case "reset": {
      workerState.reset();
      self.postMessage({
        type: "reset",
        sender: "worker",
        reqId: msg.reqId,
        payload: null,
      });
      break;
    }
  }
};

self.onmessage = (event) => {
  handleMessage(event).catch((error) => {
    console.error("Worker encountered an error:", error);
  });
};
