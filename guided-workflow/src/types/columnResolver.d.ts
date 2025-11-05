// types/columnResolver.d.ts
import type { WorkSheet } from "xlsx";

import type {
  TColumnSchema,
  TResolvedColumn,
  TUnresolvedColumn,
} from "~/domain/ColumnResolver";

type TResolveColumnsClientPayload = {
  sheet: WorkSheet;
  columns: TColumnSchema[];
};

type TResolveColumnsMessage = {
  type: "resolveColumns";
  sender: "client";
  payload: TResolveColumnsClientPayload;
  reqId: string;
};

type TResolveColumnsWorkerPayload = {
  resolvedColumns: TResolvedColumn[];
  unresolvedColumns: TUnresolvedColumn[];
  resolvedData: Record<string, unknown>[];
};

type TResolveColumnsMessageReply = {
  type: "resolveColumns";
  sender: "worker";
  payload: TResolveColumnsWorkerPayload;
  reqId: string;
};

type TColumnResolverErrorMessage = {
  type: "error";
  sender: "worker";
  payload: {
    message: string;
  };
  reqId: string;
};

type TColumnResolverClientMessage = TResolveColumnsMessage;
type TColumnResolverWorkerMessage =
  | TResolveColumnsMessageReply
  | TColumnResolverErrorMessage;

export type TypedWorker<Out, In> = Omit<
  Worker,
  "postMessage" | "onmessage" | "addEventListener"
> & {
  postMessage(message: In, transfer?: Transferable[]): void;

  addEventListener(
    type: "message",
    listener: (ev: MessageEvent<Out>) => void,
    options?: boolean | AddEventListenerOptions,
  ): void;

  onmessage: ((ev: MessageEvent<Out>) => void) | null;
};

declare module "columnResolver.worker" {
  const ColumnResolverWorkerFactory: {
    new (): TypedWorker<
      TColumnResolverWorkerMessage,
      TColumnResolverClientMessage
    >;
  };

  export default ColumnResolverWorkerFactory;
}
