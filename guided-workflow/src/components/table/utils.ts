import { capitalize } from "@mui/material";
import { common, grey } from "@mui/material/colors";
import { Column, Table } from "@tanstack/react-table";
import { CSSProperties } from "react";
import { z } from "zod";

export const getCommonPinningStyles = <T>(column: Column<T>): CSSProperties => {
  const isPinned = column.getIsPinned();
  const isLastLeftPinnedColumn =
    isPinned === "left" && column.getIsLastColumn("left");
  const isFirstRightPinnedColumn =
    isPinned === "right" && column.getIsFirstColumn("right");

  return {
    boxShadow: isLastLeftPinnedColumn
      ? `-2px 0 0px ${grey[200]} inset`
      : isFirstRightPinnedColumn
        ? `2px 0 0px ${grey[200]} inset`
        : undefined,
    left: isPinned === "left" ? `${column.getStart("left")}px` : undefined,
    right: isPinned === "right" ? `${column.getAfter("right")}px` : undefined,
    opacity: isPinned ? 0.95 : 1,
    background: isPinned ? common.white : undefined,
    position: isPinned ? "sticky" : "relative",
    zIndex: isPinned ? 1 : 0,
  };
};

export const TableMetaEnums = z.enum([
  "range",
  "select",
  "multi-select",
  "multi-select-no-facet",
  "date",
  "multi-autocomplete",
]);

const metaSchema = z.object({
  filterVariant: TableMetaEnums,
});

// meta is used within column definitions to store additional information
// currently only used for filterVariant to tell `TableFilters` which filter to render
export const getMeta = <T>(column: Column<T, unknown>) => {
  const parsed = metaSchema.safeParse(column.columnDef.meta);
  if (parsed.success) return parsed.data;
  return {
    filterVariant: undefined,
  };
};

export const getHeaderLabel = <T>(column: Column<T, unknown>) => {
  const header = column.columnDef.header;
  return typeof header === "string"
    ? header
    : capitalize(column.id.split("_").join(" "));
};

const tableMetaSchema = z.object({
  updateData: z.function(z.tuple([z.number(), z.string(), z.unknown()])),
});

export const getTableMeta = <T>(table: Table<T>) => {
  const parsed = tableMetaSchema.safeParse(table.options.meta);
  if (parsed.success) return parsed.data;
  return {
    updateData: undefined,
  };
};

export const getColumnWidth = <T>(
  table: Table<T>,
  column: Column<T, unknown>,
  containerWidth: number,
): number => {
  const columns = table.getVisibleLeafColumns();
  const columnSizes = columns.map((col) => ({
    id: col.id,
    size: col.getSize(),
  }));
  const largest = columnSizes.reduce(
    (acc, curr) => {
      return acc.size > curr.size ? acc : curr;
    },
    { id: "", size: 0 },
  );

  // if the column is the largest, return its size to give it priority in the table
  if (column.id === largest.id) {
    return largest.size;
  }
  const remainingSpace =
    containerWidth - columns.reduce((acc, curr) => acc + curr.getSize(), 0);
  const remainingColumns = columns.filter((col) => col.id !== largest.id);
  const remainingColumnsWidth = remainingColumns.reduce(
    (acc, curr) => acc + curr.getSize(),
    0,
  );

  // even distribution of column sizes
  const proposedColumnSize =
    (remainingSpace + remainingColumnsWidth) / remainingColumns.length;

  // return whichever is greater, the proposed size or the size from the column definition
  const greater = Math.max(proposedColumnSize, column.getSize());

  return greater;
};
