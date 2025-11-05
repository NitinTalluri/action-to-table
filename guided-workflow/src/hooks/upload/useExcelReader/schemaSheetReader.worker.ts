/// <reference lib="webworker" />
import type { TSchemaInferenceNamespace } from "~/domain/resolvers/schemaInferenceRegistry";
import { SchemaSheetReaderState } from "~/hooks/upload/useExcelReader/schemaSheetReaderState";
import type {
  ToSchemaWorkerMessage,
  TypedSchemaWorker,
} from "~/hooks/upload/useExcelReader/schemaSheetReaderTypes";
import invariant from "~/utils/invariant";

type Ctx = TypedSchemaWorker;

declare const self: Ctx;

let WORKER_NAMESPACE: TSchemaInferenceNamespace | null = null;
let workerState: SchemaSheetReaderState<TSchemaInferenceNamespace> | null =
  null;

const handleMessage = async (event: MessageEvent<ToSchemaWorkerMessage>) => {
  const msg = event.data;

  switch (msg.type) {
    case "setNamespace": {
      const {
        payload: { namespace },
        reqId,
      } = msg;
      WORKER_NAMESPACE = namespace;
      workerState = new SchemaSheetReaderState();
      self.postMessage({
        type: msg.type,
        sender: "worker",
        payload: { namespace },
        reqId: reqId,
      });

      break;
    }
    case "loadWorkbook": {
      const { payload: file, options, reqId } = msg;
      invariant(workerState, "Worker state is not initialized");
      invariant(WORKER_NAMESPACE, "Worker namespace is not set");

      const fileName = await workerState.loadWorkbook(
        file,
        options,
        WORKER_NAMESPACE,
      );
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
      invariant(workerState, "Worker state is not initialized");
      invariant(WORKER_NAMESPACE, "Worker namespace is not set");

      const { sheetNames } = workerState.getSheets(fileName);
      self.postMessage({
        type: msg.type,
        sender: "worker",
        payload: { fileName, sheetNames },
        reqId,
      });
      break;
    }
    case "inferSchema": {
      const {
        payload: { fileName, sheetName },
        reqId,
      } = msg;
      invariant(workerState, "Worker state is not initialized");
      invariant(WORKER_NAMESPACE, "Worker namespace is not set");

      const inferenceResult = await workerState.inferSchema(
        fileName,
        sheetName,
      );
      self.postMessage({
        type: msg.type,
        sender: "worker",
        payload: {
          inferenceResult,
          fileName,
          sheetName,
          namespace: WORKER_NAMESPACE,
        },
        reqId,
      });
      break;
    }
    case "getResolvedData": {
      const {
        payload: { fileName, sheetName },
        reqId,
      } = msg;
      invariant(workerState, "Worker state is not initialized");
      invariant(WORKER_NAMESPACE, "Worker namespace is not set");

      const { resolvedData, droppedRowCount } =
        await workerState.getResolvedData(fileName, sheetName);
      self.postMessage({
        type: msg.type,
        sender: "worker",
        payload: {
          resolvedData,
          droppedRowCount,
          fileName,
          sheetName,
          namespace: WORKER_NAMESPACE,
        },
        reqId,
      });
      break;
    }
    case "validate": {
      const {
        payload: { fileName, sheetName, reviewedData },
        reqId,
      } = msg;
      invariant(workerState, "Worker state is not initialized");
      invariant(WORKER_NAMESPACE, "Worker namespace is not set");

      await workerState.validateData(
        fileName,
        sheetName,
        reviewedData,
        0,
        reviewedData.length,
      );
      self.postMessage({
        type: msg.type,
        sender: "worker",
        payload: { fileName, sheetName, namespace: WORKER_NAMESPACE },
        reqId,
      });
      break;
    }

    case "getValidatedData": {
      const {
        payload: { fileName, sheetName },
        reqId,
      } = msg;
      invariant(workerState, "Worker state is not initialized");
      invariant(WORKER_NAMESPACE, "Worker namespace is not set");

      const { validatedRows, errors, errorTypes } =
        workerState.getValidatedData(fileName, sheetName);
      self.postMessage({
        type: msg.type,
        sender: "worker",
        payload: {
          validatedRows,
          errors,
          errorTypes,
          fileName,
          sheetName,
          namespace: WORKER_NAMESPACE,
        },
        reqId,
      });
      break;
    }

    case "reset": {
      invariant(workerState, "Worker state is not initialized");
      invariant(WORKER_NAMESPACE, "Worker namespace is not set");

      workerState.reset();
      self.postMessage({
        type: "reset",
        sender: "worker",
        payload: null,
        reqId: msg.reqId,
      });
      break;
    }

    case "resetResolvedData": {
      const {
        payload: { fileName, sheetName },
        reqId,
      } = msg;
      invariant(workerState, "Worker state is not initialized");
      invariant(WORKER_NAMESPACE, "Worker namespace is not set");

      workerState.resetResolvedData();
      self.postMessage({
        type: msg.type,
        sender: "worker",
        payload: { fileName, sheetName, namespace: WORKER_NAMESPACE },
        reqId,
      });
      break;
    }
    case "resetValidatedData": {
      const {
        payload: { fileName, sheetName },
        reqId,
      } = msg;
      invariant(workerState, "Worker state is not initialized");
      invariant(WORKER_NAMESPACE, "Worker namespace is not set");

      workerState.resetValidatedData();

      self.postMessage({
        type: msg.type,
        sender: "worker",
        payload: { fileName, sheetName, namespace: WORKER_NAMESPACE },
        reqId,
      });
      break;
    }
    default: {
      const _exhaustiveCheck: never = msg;
      throw new Error(`Unhandled message type: ${msg}`);
    }
  }
};

self.onmessage = (event) => {
  handleMessage(event).catch((error) => {
    console.error("Worker encountered an error:", error);
  });
};
