import DataGridXL from "@datagridxl/datagridxl2";
import { RefObject, useRef } from "react";

export type TDataGridRef<
  Data = unknown,
  T extends HTMLElement = HTMLDivElement,
> = T & {
  grid?: DataGridXL<Data>;
};

const useGridRef = <
  Data = unknown,
  T extends HTMLElement = HTMLDivElement,
>(): RefObject<TDataGridRef<Data, T>> => {
  return useRef<T | null>(null);
};

export default useGridRef;
