import { useCallback, useEffect, useRef, useState } from "react";

import { TColumnSchema } from "~/domain/ColumnResolver";
import { TColumnRegistryName } from "~/domain/resolvers/columnRegistry";
import {
  FromColumnWorkerMessage,
  ToColumnWorkerMessage,
  TypedColumnWorker,
} from "~/hooks/upload/useExcelReader/columnSheetReaderTypes";
import invariant from "~/utils/invariant";

type TColumnWorker = TypedColumnWorker<
  FromColumnWorkerMessage,
  ToColumnWorkerMessage
>;
type TColumnWorkerReplyPayload = FromColumnWorkerMessage["payload"];
type TColumnMessagePayloadMap = {
  [K in FromColumnWorkerMessage["type"]]: Extract<
    FromColumnWorkerMessage,
    { type: K }
  >["payload"];
};

const defaultOptions = {
  dense: true,
  type: "buffer" as const,
  cellDates: true,
};

const createRequestHandler = <T extends FromColumnWorkerMessage["type"]>(
  type: T,
  resolve: (value: TColumnMessagePayloadMap[T]) => void,
  reject: (reason?: Error) => void,
) => {
  return {
    resolve: (payload: TColumnWorkerReplyPayload) => {
      resolve(payload as TColumnMessagePayloadMap[T]);
    },
    reject,
  };
};

export type TColumnSheetReaderFunctions = ReturnType<
  typeof useColumnSheetReader
>;

export const useColumnSheetReader = () => {
  const workerRef = useRef<TColumnWorker | null>(null);
  const workerRefToken = useRef(0);
  const [stateToken, setStateToken] = useState(0);
  const inFlightRequests = useRef<
    Map<
      string,
      {
        resolve: (value: TColumnWorkerReplyPayload) => void;
        reject: (reason?: Error) => void;
      }
    >
  >(new Map());

  useEffect(() => {
    const requests = inFlightRequests.current;
    if (workerRef.current && workerRefToken.current !== stateToken) {
      console.log(
        `Terminating worker due to state token change ${stateToken} !== ${workerRefToken.current}`,
      );
      workerRef.current.onmessage = null;
      workerRef.current.terminate();
      workerRef.current = null;
      requests.forEach((entry) => {
        console.error(`Rejecting pending request ${entry} due to worker reset`);
        entry.reject(new Error("Worker terminated before response"));
      });
    } else if (workerRef.current) {
      return;
    }
    workerRef.current = new Worker(
      new URL("./columnSheetReader.worker.ts", import.meta.url),
      { type: "module" },
    ) as TColumnWorker;

    workerRefToken.current = stateToken;
    workerRef.current.onmessage = (event) => {
      const msg = event.data;
      const entry = inFlightRequests.current.get(msg.reqId);
      if (!entry) return;
      inFlightRequests.current.delete(msg.reqId);
      entry.resolve(msg.payload);
    };
    return () => {
      if (workerRef.current) {
        workerRef.current.onmessage = null;
        workerRef.current.terminate();
        workerRef.current = null;
        requests.forEach((entry) => {
          entry.reject(new Error("Worker terminated before response"));
        });
      }
    };
  }, [stateToken]);

  const loadWorkbook = useCallback((file: File) => {
    invariant(workerRef.current, "Worker is not initialized");
    const requestId = crypto.randomUUID();

    return new Promise<TColumnMessagePayloadMap["loadWorkbook"]>(
      (resolve, reject) => {
        inFlightRequests.current.set(
          requestId,
          createRequestHandler("loadWorkbook", resolve, reject),
        );

        // Post the message to the worker
        workerRef.current!.postMessage({
          type: "loadWorkbook",
          sender: "client",
          payload: file,
          options: defaultOptions,
          reqId: requestId,
        });
      },
    );
  }, []);

  const getSheets = useCallback((params: { fileName: string }) => {
    invariant(workerRef.current, "Worker is not initialized");
    const { fileName } = params;
    const requestId = crypto.randomUUID();
    return new Promise<TColumnMessagePayloadMap["getSheets"]>(
      (resolve, reject) => {
        inFlightRequests.current.set(
          requestId,
          createRequestHandler("getSheets", resolve, reject),
        );

        // Post the message to the worker
        workerRef.current!.postMessage({
          type: "getSheets",
          sender: "client",
          payload: { fileName },
          reqId: requestId,
        });
      },
    );
  }, []);

  const getResolvedColumns = useCallback(
    (params: {
      fileName: string;
      sheetName: string;
      schema: TColumnSchema[];
    }) => {
      invariant(workerRef.current, "Worker is not initialized");
      const { fileName, sheetName, schema } = params;
      const requestId = crypto.randomUUID();
      return new Promise<TColumnMessagePayloadMap["getResolvedColumns"]>(
        (resolve, reject) => {
          inFlightRequests.current.set(
            requestId,
            createRequestHandler("getResolvedColumns", resolve, reject),
          );

          // Post the message to the worker
          workerRef.current!.postMessage({
            type: "getResolvedColumns",
            sender: "client",
            payload: { fileName, sheetName, schema },
            reqId: requestId,
          });
        },
      );
    },
    [],
  );

  const getResolvedData = useCallback(
    (params: {
      fileName: string;
      sheetName: string;
      schema: TColumnSchema[];
    }) => {
      invariant(workerRef.current, "Worker is not initialized");
      const { fileName, sheetName, schema } = params;
      const requestId = crypto.randomUUID();
      return new Promise<TColumnMessagePayloadMap["getResolvedData"]>(
        (resolve, reject) => {
          inFlightRequests.current.set(
            requestId,
            createRequestHandler("getResolvedData", resolve, reject),
          );
          workerRef.current!.postMessage({
            type: "getResolvedData",
            sender: "client",
            payload: { fileName, sheetName, schema },
            reqId: requestId,
          });
        },
      );
    },
    [],
  );

  const validateData = useCallback(
    (params: {
      fileName: string;
      sheetName: string;
      reviewedData: Record<string, unknown>[];
      registryName: TColumnRegistryName;
    }) => {
      invariant(workerRef.current, "Worker is not initialized");
      const { fileName, sheetName, registryName, reviewedData } = params;
      const requestId = crypto.randomUUID();
      return new Promise<TColumnMessagePayloadMap["validateData"]>(
        (resolve, reject) => {
          inFlightRequests.current.set(
            requestId,
            createRequestHandler("validateData", resolve, reject),
          );
          workerRef.current!.postMessage({
            type: "validateData",
            sender: "client",
            payload: { fileName, sheetName, registryName, reviewedData },
            reqId: requestId,
          });
        },
      );
    },
    [],
  );

  const getValidatedData = useCallback(
    (params: { fileName: string; sheetName: string }) => {
      invariant(workerRef.current, "Worker is not initialized");
      const { fileName, sheetName } = params;
      const requestId = crypto.randomUUID();
      return new Promise<TColumnMessagePayloadMap["getValidatedData"]>(
        (resolve, reject) => {
          inFlightRequests.current.set(
            requestId,
            createRequestHandler("getValidatedData", resolve, reject),
          );
          workerRef.current!.postMessage({
            type: "getValidatedData",
            sender: "client",
            payload: { fileName, sheetName },
            reqId: requestId,
          });
        },
      );
    },
    [],
  );

  const clearResolvedData = useCallback(() => {
    invariant(workerRef.current, "Worker is not initialized");
    const requestId = crypto.randomUUID();
    return new Promise<TColumnMessagePayloadMap["clearResolvedData"]>(
      (resolve, reject) => {
        inFlightRequests.current.set(
          requestId,
          createRequestHandler("clearResolvedData", resolve, reject),
        );
        workerRef.current!.postMessage({
          type: "clearResolvedData",
          sender: "client",
          payload: null,
          reqId: requestId,
        });
      },
    );
  }, []);
  const resetWorker = useCallback(() => {
    invariant(workerRef.current, "Worker is not initialized");
    const requestId = crypto.randomUUID();
    return new Promise<TColumnMessagePayloadMap["reset"]>((resolve, reject) => {
      inFlightRequests.current.set(
        requestId,
        createRequestHandler("reset", resolve, reject),
      );
      workerRef.current!.postMessage({
        type: "reset",
        sender: "client",
        payload: null,
        reqId: requestId,
      });
    });
  }, []);

  const reset = useCallback(() => {
    setStateToken((t) => t + 1);
  }, []);

  return {
    loadWorkbook,
    getSheets,
    getResolvedColumns,
    getResolvedData,
    clearResolvedData,
    validateData,
    getValidatedData,
    resetWorker,
    reset,
  };
};
