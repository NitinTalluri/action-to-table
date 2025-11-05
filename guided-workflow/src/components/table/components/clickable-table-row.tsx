import { PaletteColor, TableCell, TableRow, Theme } from "@mui/material";
import { Column, flexRender, Row } from "@tanstack/react-table";
import { VirtualItem, Virtualizer } from "@tanstack/react-virtual";

import { getCommonPinningStyles } from "../utils";

export const ClickableRow = <T,>({
  virtualRow,
  rowVirtualizer,
  row,
  onClick,
  getColWidth,
  rowBorderColor,
  isSelected = false,
}: {
  virtualRow: VirtualItem;
  rowVirtualizer: Virtualizer<HTMLDivElement, Element>;
  row: Row<T>;
  getColWidth: (column: Column<T>) => number | string;
  onClick: (data: T) => void;
  rowBorderColor?: string;
  isSelected?: boolean;
}) => {
  const getColor = (theme: Theme, colorKey: keyof Theme["palette"]) => {
    const color = theme.palette[colorKey] as PaletteColor | undefined;
    return color?.main || "";
  };

  return (
    <TableRow
      data-index={virtualRow.index} //needed for dynamic row height measurement
      ref={(node) => rowVirtualizer.measureElement(node)} //measure dynamic row height
      style={{
        display: "flex",
        position: "absolute",
        transform: `translateY(${virtualRow.start}px)`, //this should always be a `style` as it changes on scroll
        width: "100%",
      }}
      sx={(theme) => ({
        backgroundColor: isSelected ? theme.palette.action.selected : "",
        borderLeft: rowBorderColor && 6,
        borderColor: getColor(theme, rowBorderColor as keyof Theme["palette"]),
      })}
      onClick={() => onClick(row.original)}
      hover
    >
      {row.getVisibleCells().map((cell) => {
        return (
          <TableCell
            key={cell.id}
            style={{
              display: "flex",
              alignItems: "center",
              width: getColWidth(cell.column),
              ...getCommonPinningStyles(cell.column),
            }}
          >
            {flexRender(cell.column.columnDef.cell, cell.getContext())}
          </TableCell>
        );
      })}
    </TableRow>
  );
};
