// types/sheetReader.d.ts

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

declare module "sheetReader.worker" {
  const SheetReaderWorkerFactory: {
    new (): TypedWorker<FromWorker, ToWorker>;
  };

  export default SheetReaderWorkerFactory;
}
