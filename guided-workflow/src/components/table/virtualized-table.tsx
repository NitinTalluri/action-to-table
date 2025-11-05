import {
  Box,
  Button,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from "@mui/material";
import {
  Column,
  flexRender,
  Header,
  Row,
  Table as ITable,
} from "@tanstack/react-table";
import {
  useVirtualizer,
  VirtualItem,
  Virtualizer,
} from "@tanstack/react-virtual";
import { ReactNode, useRef } from "react";

import { useContainerDimensions } from "~/hooks/useContainerDimensions";

import { HeaderCell } from "./components";
import { getColumnWidth, getCommonPinningStyles } from "./utils";

export const VirtualizedTable = <T,>({
  table,
  renderHeader,
  renderRow,
  maxHeight,
  minHeight,
}: {
  table: ITable<T>;
  renderHeader?: (props: {
    header: Header<T, unknown>;
    getColumnWidth: (column: Column<T>) => number | string;
  }) => ReactNode;
  renderRow?: (props: {
    virtualRow: VirtualItem;
    rowVirtualizer: Virtualizer<HTMLDivElement, Element>;
    row: Row<T>;
    getColWidth: (column: Column<T>) => number | string;
  }) => ReactNode;
  maxHeight?: string | number;
  minHeight?: string | number;
}) => {
  const { rows } = table.getRowModel();

  //The virtualizer needs to know the scrollable container element
  const tableContainerRef = useRef<HTMLDivElement>(null);

  const rowVirtualizer = useVirtualizer({
    count: rows?.length,
    estimateSize: () => 33, //estimate row height for accurate scrollbar dragging
    getScrollElement: () => tableContainerRef.current,
    //measure dynamic row height, except in firefox because it measures table border height incorrectly
    measureElement:
      typeof window !== "undefined" &&
      navigator.userAgent.indexOf("Firefox") === -1
        ? (element) => element?.getBoundingClientRect().height
        : undefined,
    overscan: 5,
  });

  const { ref: containerRef, domRect } = useContainerDimensions();

  const containerHeight = maxHeight
    ? maxHeight
    : `calc(100vh - ${domRect?.top || 0}px - 1rem)`;

  // if no rows and a global or column filter is present, show empty table message
  const showEmptyTableMessage =
    table.getRowCount() === 0 &&
    (table.getState().columnFilters?.length ||
      table.getState().globalFilter?.length);

  return (
    <Box
      ref={containerRef}
      sx={(theme) => ({ backgroundColor: theme.palette.common.white })}
    >
      <TableContainer
        ref={tableContainerRef}
        style={{
          overflow: "auto", //our scrollable table container
          position: "relative", //needed for sticky header
          maxHeight: containerHeight,
          minHeight: minHeight || 300,
        }}
      >
        <Table
          style={{
            borderCollapse: "separate",
            margin: "0 auto",
          }}
          size="small"
        >
          <TableHead
            style={{
              display: "grid",
              position: "sticky",
              top: 0,
              zIndex: 1,
            }}
          >
            {table.getHeaderGroups().map((headerGroup) => (
              <TableRow
                key={headerGroup.id}
                style={{ display: "flex", width: "100%" }}
              >
                {headerGroup.headers.map((header) => {
                  if (renderHeader) {
                    return renderHeader({
                      header,
                      getColumnWidth: (col) =>
                        getColumnWidth(table, col, domRect?.width || 0),
                    });
                  }
                  return (
                    <HeaderCell
                      key={header.id}
                      table={table}
                      header={header}
                      width={getColumnWidth(
                        table,
                        header.column,
                        domRect?.width || 0,
                      )}
                    />
                  );
                })}
              </TableRow>
            ))}
          </TableHead>
          <TableBody
            style={{
              display: "grid",
              height: `${rowVirtualizer.getTotalSize()}px`, //tells scrollbar how big the table is
              position: "relative", //needed for absolute positioning of rows
            }}
          >
            {rowVirtualizer.getVirtualItems().map((virtualRow) => {
              const row = rows[virtualRow.index];
              if (renderRow) {
                return renderRow({
                  virtualRow,
                  rowVirtualizer,
                  row,
                  getColWidth: (column) =>
                    getColumnWidth(table, column, domRect?.width || 0),
                });
              }
              return (
                <TableRow
                  data-index={virtualRow.index} //needed for dynamic row height measurement
                  ref={(node) => rowVirtualizer.measureElement(node)} //measure dynamic row height
                  key={row.id}
                  style={{
                    display: "flex",
                    position: "absolute",
                    transform: `translateY(${virtualRow.start}px)`, //this should always be a `style` as it changes on scroll
                    width: "100%",
                  }}
                  hover
                >
                  {row.getVisibleCells().map((cell) => {
                    return (
                      <TableCell
                        key={cell.id}
                        style={{
                          ...getCommonPinningStyles(cell.column),
                          display: "flex",
                          alignItems: "center",
                          width: getColumnWidth(
                            table,
                            cell.column,
                            domRect?.width || 0,
                          ),
                        }}
                      >
                        {flexRender(
                          cell.column.columnDef.cell,
                          cell.getContext(),
                        )}
                      </TableCell>
                    );
                  })}
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </TableContainer>
      {showEmptyTableMessage ? (
        <Stack sx={{ padding: 1, alignItems: "center", gap: 1 }}>
          <Stack sx={{ alignItems: "center" }}>
            <Typography>
              We couldn't find any results with your selected filters.
            </Typography>
            <Typography variant="body2">Try adjusting your filters.</Typography>
          </Stack>
          <Button
            variant="outlined"
            onClick={() => {
              table.setColumnFilters([]);
              table.setGlobalFilter("");
            }}
          >
            Clear filters
          </Button>
        </Stack>
      ) : null}
    </Box>
  );
};
