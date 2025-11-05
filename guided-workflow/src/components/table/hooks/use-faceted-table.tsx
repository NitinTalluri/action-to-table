import {
  getFacetedMinMaxValues,
  getFacetedRowModel,
  getFacetedUniqueValues,
  getFilteredRowModel,
  TableOptions,
} from "@tanstack/react-table";
import { z } from "zod";

import { isValidDateString } from "../components/filters/utils";
import { useTypedTable } from "./useTypedTable";

const basicArraySchema = z.array(
  z.union([z.string(), z.number(), z.boolean()]),
);
const isBasicArray = (
  value: unknown,
): value is Array<string | number | boolean> => {
  return basicArraySchema.safeParse(value).success;
};

export const useFacetedTable = <T,>(
  options: Omit<TableOptions<T>, "getCoreRowModel" | "filterFns">,
) => {
  return useTypedTable({
    columnResizeMode: "onChange",
    getFilteredRowModel: getFilteredRowModel(),
    getFacetedRowModel: getFacetedRowModel(),
    getFacetedUniqueValues: getFacetedUniqueValues(),
    getFacetedMinMaxValues: getFacetedMinMaxValues(),
    enableMultiSort: true,
    // supplies a default cell renderer for basic types
    // can be overwritten in the column definition
    defaultColumn: {
      cell: (info) => {
        const value = info.getValue();
        if (!value) return "--";
        if (isBasicArray(value)) {
          return value.join(", ");
        }
        if (isValidDateString(value)) {
          return new Date(value).toLocaleDateString(undefined, {
            year: "numeric",
            month: "2-digit",
            day: "2-digit",
            timeZone: "UTC",
          });
        }
        return value;
      },
    },
    ...options,
  });
};
