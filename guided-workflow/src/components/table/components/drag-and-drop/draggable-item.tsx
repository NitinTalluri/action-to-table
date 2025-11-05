import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import DragHandleIcon from "@mui/icons-material/DragHandle";
import { Box, Checkbox, FormLabel, Stack, Typography } from "@mui/material";
import { Column } from "@tanstack/react-table";
import { ReactNode } from "react";

import { getHeaderLabel } from "../../utils";

export const DraggableItem = <T,>({ column }: { column: Column<T> }) => {
  const { attributes, isDragging, listeners, setNodeRef, transform } =
    useSortable({
      id: column.id,
    });

  return (
    <Stack
      ref={setNodeRef}
      sx={(theme) => ({
        backgroundColor: theme.palette.background.paper,
        // translate instead of transform to avoid squishing
        transform: CSS.Translate.toString(transform),
        paddingRight: 1,
        borderRadius: 1,
        zIndex: isDragging ? 1 : 0,
      })}
    >
      <ColumnItem column={column} isDragging={isDragging}>
        <Box
          sx={{
            display: "flex",
            justifyContent: "center",
          }}
          {...attributes}
          {...listeners}
        >
          <DragHandleIcon sx={{ cursor: "grab" }} />
        </Box>
      </ColumnItem>
    </Stack>
  );
};

export const ColumnItem = <T,>({
  column,
  isDragging,
  children,
}: {
  column: Column<T>;
  isDragging?: boolean;
  children?: ReactNode;
}) => {
  const label = getHeaderLabel(column);
  return (
    <Stack
      direction="row"
      sx={[
        {
          gap: 1,
          alignItems: "center",
          justifyContent: "space-between",
        },
        (theme) => ({
          position: "relative",
          backgroundColor: theme.palette.background.paper,
          paddingRight: 1,
          borderRadius: 1,
          overflow: "hidden",
          ":hover": {
            backgroundColor: theme.palette.grey[100],
          },
        }),
      ]}
    >
      <FormLabel
        sx={{
          display: "flex",
          alignItems: "center",
        }}
      >
        <Checkbox
          checked={column.getIsVisible()}
          onChange={column.getToggleVisibilityHandler()}
        />
        <Typography>{label}</Typography>
      </FormLabel>
      {children}
      {isDragging ? (
        <Box
          sx={(theme) => ({
            position: "absolute",
            top: 0,
            left: 0,
            bottom: 0,
            right: 0,
            zIndex: 1,
            backgroundColor: theme.palette.grey[200],
          })}
        />
      ) : null}
    </Stack>
  );
};
