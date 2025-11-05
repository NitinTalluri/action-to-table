import { UniqueIdentifier, useDroppable } from "@dnd-kit/core";
import {
  SortableContext,
  verticalListSortingStrategy,
} from "@dnd-kit/sortable";
import { Box, Stack, Typography } from "@mui/material";
import { Column } from "@tanstack/react-table";

import { DraggableItem } from "./draggable-item";

export const DroppableArea = <T,>({
  id,
  items,
  columns,
}: {
  id: string;
  items: UniqueIdentifier[];
  columns: Column<T>[];
}) => {
  const { setNodeRef } = useDroppable({
    id: id,
  });

  const label =
    id === "start" ? "Pinned to start" : id === "end" ? "Pinned to end" : "";
  return (
    <div>
      <SortableContext
        items={items}
        strategy={verticalListSortingStrategy}
        id={id}
      >
        <div ref={setNodeRef}>
          <Stack
            sx={{
              padding: 1,
            }}
          >
            <Typography variant="caption">{label}</Typography>
            {items.length ? (
              items.map((columnId) => {
                const column = columns.find((col) => col.id === columnId);
                if (!column) {
                  return null;
                }
                return <DraggableItem key={columnId} column={column} />;
              })
            ) : (
              <Box
                sx={(theme) => ({
                  padding: 1,
                  borderStyle: "dashed",
                  borderColor: theme.palette.divider,
                  borderWidth: 1,
                  borderRadius: 1,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  height: 42,
                })}
              >
                <Typography
                  variant="caption"
                  sx={{
                    color: "text.disabled",
                  }}
                >
                  Drag columns here to pin to {id}
                </Typography>
              </Box>
            )}
          </Stack>
        </div>
      </SortableContext>
    </div>
  );
};
