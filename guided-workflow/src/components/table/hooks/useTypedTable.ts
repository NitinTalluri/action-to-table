import {
  FilterFn,
  getCoreRowModel,
  getSortedRowModel,
  TableOptions,
  useReactTable,
} from "@tanstack/react-table";
import { useMemo } from "react";

import { dateBetweenFilterFn, multiSelectFilterFn } from "../custom-filter-fns";

declare module "@tanstack/table-core" {
  // eslint-disable-next-line @typescript-eslint/no-empty-object-type
  interface FilterFns
    extends Partial<{
      dateBetweenFilterFn?: FilterFn<unknown>;
      multiSelectFilterFn?: FilterFn<unknown>;
    }> {}
}

// A very basic wrapper on top of useReactTable that sets up some defaults
export function useTypedTable<T>(
  options: Omit<TableOptions<T>, "getCoreRowModel" | "filterFns">,
) {
  return useReactTable({
    filterFns: {
      dateBetweenFilterFn,
      multiSelectFilterFn,
    },
    columnResizeMode: "onChange",
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    ...useMemo(() => options, [options]),
  });
}
