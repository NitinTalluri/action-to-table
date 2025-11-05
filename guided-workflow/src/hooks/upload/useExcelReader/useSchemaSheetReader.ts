import { useCallback, useEffect, useRef, useState } from "react";

import { TSchemaInferenceNamespace } from "~/domain/resolvers/schemaInferenceRegistry";
import {
  FromSchemaWorkerMessage,
  ToSchemaWorkerMessage,
  TypedSchemaWorker,
} from "~/hooks/upload/useExcelReader/schemaSheetReaderTypes";
import invariant from "~/utils/invariant";

type TSchemaWorker = TypedSchemaWorker<
  FromSchemaWorkerMessage,
  ToSchemaWorkerMessage
>;
type TSchemaWorkerReplyPayload = FromSchemaWorkerMessage["payload"];
type TSchemaMessagePayloadMap = {
  [K in FromSchemaWorkerMessage["type"]]: Extract<
    FromSchemaWorkerMessage,
    { type: K }
  >["payload"];
};

type TGenericData = Record<string, unknown>;

const defaultOptions = {
  dense: true,
  type: "buffer" as const,
  cellDates: true,
};

const createRequestHandler = <T extends FromSchemaWorkerMessage["type"]>(
  type: T,
  resolve: (value: TSchemaMessagePayloadMap[T]) => void,
  reject: (reason?: Error) => void,
) => {
  return {
    resolve: (payload: TSchemaWorkerReplyPayload) => {
      resolve(payload as TSchemaMessagePayloadMap[T]);
    },
    reject,
  };
};

export type TSchemaSheetReaderFunctions<
  N extends TSchemaInferenceNamespace = TSchemaInferenceNamespace,
> = ReturnType<typeof useSchemaSheetReader<N>> & { namespace: N };

export const useSchemaSheetReader = <N extends TSchemaInferenceNamespace>({
  namespace,
}: {
  namespace: N;
}) => {
  const workerRef = useRef<TSchemaWorker | null>(null);
  const workerRefToken = useRef(0);
  const [stateToken, setStateToken] = useState(0);
  const inFlightRequests = useRef<
    Map<
      string,
      {
        resolve: (value: TSchemaWorkerReplyPayload) => void;
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
      new URL("./schemaSheetReader.worker.ts", import.meta.url),
      {
        type: "module",
      },
    ) as TSchemaWorker;

    workerRefToken.current = stateToken;
    setNamespace(namespace);
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
  }, [namespace, stateToken]);

  const setNamespace = (namespace: TSchemaInferenceNamespace) => {
    // Private method
    invariant(workerRef.current, "Worker is not initialized");
    const requestId = crypto.randomUUID();
    workerRef.current.postMessage({
      type: "setNamespace",
      sender: "client",
      payload: { namespace },
      reqId: requestId,
    });
  };

  const loadWorkbook = useCallback((file: File) => {
    invariant(workerRef.current, "Worker is not initialized");
    const requestId = crypto.randomUUID();

    return new Promise<TSchemaMessagePayloadMap["loadWorkbook"]>(
      (resolve, reject) => {
        inFlightRequests.current.set(
          requestId,
          createRequestHandler("loadWorkbook", resolve, reject),
        );
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
    return new Promise<TSchemaMessagePayloadMap["getSheets"]>(
      (resolve, reject) => {
        inFlightRequests.current.set(
          requestId,
          createRequestHandler("getSheets", resolve, reject),
        );
        workerRef.current!.postMessage({
          type: "getSheets",
          sender: "client",
          payload: { fileName },
          reqId: requestId,
        });
      },
    );
  }, []);

  const inferSchema = useCallback(
    (params: { fileName: string; sheetName: string }) => {
      invariant(workerRef.current, "Worker is not initialized");
      const { fileName, sheetName } = params;
      const requestId = crypto.randomUUID();
      return new Promise<TSchemaMessagePayloadMap["inferSchema"]>(
        (resolve, reject) => {
          inFlightRequests.current.set(
            requestId,
            createRequestHandler("inferSchema", resolve, reject),
          );
          workerRef.current!.postMessage({
            type: "inferSchema",
            reqId: requestId,
            sender: "client",
            payload: { fileName, sheetName, namespace },
          });
        },
      );
    },
    [namespace],
  );

  const getResolvedData = useCallback(
    (params: { fileName: string; sheetName: string }) => {
      invariant(workerRef.current, "Worker is not initialized");
      const { fileName, sheetName } = params;
      const requestId = crypto.randomUUID();
      return new Promise<TSchemaMessagePayloadMap["getResolvedData"]>(
        (resolve, reject) => {
          inFlightRequests.current.set(
            requestId,
            createRequestHandler("getResolvedData", resolve, reject),
          );
          workerRef.current!.postMessage({
            type: "getResolvedData",
            reqId: requestId,
            sender: "client",
            payload: { fileName, sheetName, namespace },
          });
        },
      );
    },
    [namespace],
  );

  const validate = useCallback(
    (params: {
      fileName: string;
      sheetName: string;
      reviewedData: TGenericData[];
    }) => {
      invariant(workerRef.current, "Worker is not initialized");
      const { fileName, sheetName, reviewedData } = params;
      const requestId = crypto.randomUUID();
      return new Promise<TSchemaMessagePayloadMap["validate"]>(
        (resolve, reject) => {
          inFlightRequests.current.set(
            requestId,
            createRequestHandler("validate", resolve, reject),
          );
          workerRef.current!.postMessage({
            type: "validate",
            reqId: requestId,
            sender: "client",
            payload: { fileName, sheetName, reviewedData, namespace },
          });
        },
      );
    },
    [namespace],
  );

  const getValidatedData = useCallback(
    (params: { fileName: string; sheetName: string }) => {
      invariant(workerRef.current, "Worker is not initialized");
      const { fileName, sheetName } = params;
      const requestId = crypto.randomUUID();
      return new Promise<TSchemaMessagePayloadMap["getValidatedData"]>(
        (resolve, reject) => {
          inFlightRequests.current.set(
            requestId,
            createRequestHandler("getValidatedData", resolve, reject),
          );
          workerRef.current!.postMessage({
            type: "getValidatedData",
            reqId: requestId,
            sender: "client",
            payload: { fileName, sheetName, namespace },
          });
        },
      );
    },
    [namespace],
  );

  const resetWorker = useCallback(() => {
    invariant(workerRef.current, "Worker is not initialized");
    const requestId = crypto.randomUUID();
    return new Promise<TSchemaMessagePayloadMap["reset"]>((resolve, reject) => {
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
    return resetWorker();
  }, [resetWorker]);

  const resetValidatedData = useCallback(
    (params: { fileName: string; sheetName: string }) => {
      invariant(workerRef.current, "Worker is not initialized");
      const { fileName, sheetName } = params;
      const requestId = crypto.randomUUID();
      return new Promise<TSchemaMessagePayloadMap["resetValidatedData"]>(
        (resolve, reject) => {
          inFlightRequests.current.set(
            requestId,
            createRequestHandler("resetValidatedData", resolve, reject),
          );
          workerRef.current!.postMessage({
            type: "resetValidatedData",
            reqId: requestId,
            sender: "client",
            payload: { fileName, sheetName, namespace },
          });
        },
      );
    },
    [namespace],
  );

  const resetResolvedData = useCallback(
    (params: { fileName: string; sheetName: string }) => {
      invariant(workerRef.current, "Worker is not initialized");
      const { fileName, sheetName } = params;
      const requestId = crypto.randomUUID();

      return new Promise<TSchemaMessagePayloadMap["resetResolvedData"]>(
        (resolve, reject) => {
          inFlightRequests.current.set(
            requestId,
            createRequestHandler("resetResolvedData", resolve, reject),
          );
          workerRef.current!.postMessage({
            type: "resetResolvedData",
            reqId: requestId,
            sender: "client",
            payload: { fileName, sheetName, namespace },
          });
        },
      );
    },
    [namespace],
  );

  return {
    loadWorkbook,
    getSheets,
    inferSchema,
    getResolvedData,
    resetResolvedData,
    validate,
    getValidatedData,
    resetValidatedData,
    reset,
    resetWorker,
    namespace,
  };
};
