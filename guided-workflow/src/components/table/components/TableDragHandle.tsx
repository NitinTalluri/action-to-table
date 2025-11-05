import { Box } from "@mui/material";
import { MouseEvent, TouchEvent } from "react";

export const TableDragHandle = ({
  resizeHandler,
}: {
  resizeHandler: (
    e: MouseEvent<HTMLDivElement> | TouchEvent<HTMLDivElement>,
  ) => void;
}) => (
  <Box
    onMouseDown={resizeHandler}
    onTouchStart={resizeHandler}
    sx={(theme) => ({
      position: "absolute",
      right: 0,
      top: "50%",
      height: "75%",
      transform: "translateY(-50%)",
      borderRadius: 50,
      width: 3,
      cursor: "col-resize",
      touchAction: "none",
      userSelect: "none",
      backgroundColor: theme.palette.action.hover,
      "&:hover": {
        backgroundColor: theme.palette.action.active,
      },
    })}
  />
);
