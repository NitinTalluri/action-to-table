import { TableCell, TableSortLabel } from "@mui/material";
import { flexRender, Header, Table } from "@tanstack/react-table";

import { getCommonPinningStyles } from "../utils";
import { SortIndicator } from "./sort-indicator";
import { TableDragHandle } from "./TableDragHandle";

export const HeaderCell = <T,>({
  header,
  width,
  table,
}: {
  header: Header<T, unknown>;
  width: number;
  table: Table<T>;
}) => {
  const isMultiSorting = table.getState().sorting.length > 1;
  const isSorted = header.column.getIsSorted();
  const sortIndex = table
    .getState()
    .sorting.findIndex((sort) => sort.id === header.column.id);
  const sortDirection =
    isSorted === "asc" ? "asc" : isSorted === "desc" ? "desc" : undefined;

  return (
    <TableCell
      sx={(theme) => ({
        width,
        position: "relative",
        ...getCommonPinningStyles(header.column),
        opacity: 1,
        backgroundColor: theme.palette.background.paper,
        color: theme.palette.getContrastText(theme.palette.background.paper),
      })}
      sortDirection={sortDirection}
    >
      {header.column.getCanSort() ? (
        <TableSortLabel
          active={Boolean(sortDirection)}
          direction={sortDirection || undefined}
          onClick={header.column.getToggleSortingHandler()}
        >
          {flexRender(header.column.columnDef.header, header.getContext())}
          {isMultiSorting && sortDirection && isSorted ? (
            <SortIndicator index={sortIndex} />
          ) : null}
        </TableSortLabel>
      ) : (
        flexRender(header.column.columnDef.header, header.getContext())
      )}
      {header.column.getCanResize() ? (
        <TableDragHandle resizeHandler={header.getResizeHandler()} />
      ) : null}
    </TableCell>
  );
};
