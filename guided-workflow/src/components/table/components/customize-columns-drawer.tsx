import {
  closestCenter,
  DndContext,
  type DragEndEvent,
  DragOverEvent,
  DragOverlay,
  DragStartEvent,
  KeyboardSensor,
  MeasuringStrategy,
  MouseSensor,
  TouchSensor,
  UniqueIdentifier,
  useSensor,
  useSensors,
} from "@dnd-kit/core";
import {
  restrictToVerticalAxis,
  restrictToWindowEdges,
} from "@dnd-kit/modifiers";
import { arrayMove, sortableKeyboardCoordinates } from "@dnd-kit/sortable";
import Close from "@mui/icons-material/Close";
import DragHandleIcon from "@mui/icons-material/DragHandle";
import ViewColumnIcon from "@mui/icons-material/ViewColumn";
import {
  Button,
  Card,
  Divider,
  Drawer,
  IconButton,
  Stack,
  Tooltip,
  Typography,
} from "@mui/material";
import {
  Column,
  ColumnOrderState,
  ColumnPinningState,
  OnChangeFn,
} from "@tanstack/react-table";
import { useCallback, useEffect, useRef, useState } from "react";

import { ColumnItem } from "./drag-and-drop/draggable-item";
import { DroppableArea } from "./drag-and-drop/droppable-area";

export const CustomizeColumnsDrawer = <T,>({
  columns,
  columnOrder,
  onColumnOrderChange,
  onColumnPinningChange,
  onReset,
}: {
  columns: Column<T>[];
  columnOrder: string[];
  onColumnOrderChange: OnChangeFn<ColumnOrderState>;
  onColumnPinningChange: OnChangeFn<ColumnPinningState>;
  onReset: () => void;
}) => {
  const [open, setOpen] = useState(false);

  const [items, setItems] = useState<Record<string, UniqueIdentifier[]>>({
    start: [],
    end: [],
    unpinned: [],
  });

  // Initialize the items state with the column order
  // using an effect incase the columns change externally
  useEffect(() => {
    // remove any potential duplicates
    const cleanedColumns = [...new Set(columnOrder)];
    const unpinnedColumns = cleanedColumns.filter(
      (col) => columns.find((c) => c.id === col)?.getIsPinned() === false,
    );
    const leftPinnedColumns = columns
      .filter((col) => col?.getIsPinned() === "left")
      .map((col) => col.id);
    const rightPinnedColumns = columns
      .filter((col) => col?.getIsPinned() === "right")
      .map((col) => col.id);
    setItems({
      start: leftPinnedColumns,
      end: rightPinnedColumns,
      unpinned: unpinnedColumns,
    });
  }, [columnOrder, columns]);

  // Use the defined sensors for drag and drop operation
  const sensors = useSensors(
    useSensor(MouseSensor, {
      activationConstraint: {
        // Require mouse to move 5px to start dragging, this allow onClick to be triggered on click
        distance: 5,
      },
    }),
    useSensor(TouchSensor, {
      activationConstraint: {
        // Require mouse to move 5px to start dragging, this allow onClick to be triggered on click
        tolerance: 5,
        // Require to press for 100ms to start dragging, this can reduce the chance of dragging accidentally due to page scroll
        delay: 100,
      },
    }),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    }),
  );

  // State to keep track of currently active (being dragged) item
  const [activeId, setActiveId] = useState<UniqueIdentifier | null>(null);

  // Ref to track if an item was just moved to a new container
  const recentlyMovedToNewContainer = useRef(false);

  // Function to find which container an item belongs to
  const findContainer = useCallback(
    (id: UniqueIdentifier) => {
      // if the id is a container id itself
      if (id in items) return id;

      // find the container by looking into each of them
      return Object.keys(items).find((key) => items[key].includes(id));
    },
    [items],
  );

  // Ref to store the state of items before a drag operation begins
  const itemsBeforeDrag = useRef<null | Record<string, UniqueIdentifier[]>>(
    null,
  );

  const handleDragStart = useCallback(
    ({ active }: DragStartEvent) => {
      // Store the current state of items
      itemsBeforeDrag.current = { ...items };
      // Set the active (dragged) item id
      setActiveId(active.id);
    },
    [items],
  );

  const handleDragOver = useCallback(
    ({ active, over }: DragOverEvent) => {
      if (!over || active.id in items) {
        return;
      }

      const { id: activeId } = active;
      const { id: overId } = over;

      const activeContainer = findContainer(activeId);
      const overContainer = findContainer(overId);

      if (!overContainer || !activeContainer) {
        return;
      }

      if (activeContainer !== overContainer) {
        setItems((items) => {
          const activeItems = items[activeContainer] || [];
          const overItems = items[overContainer] || [];
          const overIndex = overItems.indexOf(overId);
          const activeIndex = activeItems.indexOf(activeId);

          let newIndex: number;

          const isBelowOverItem =
            over &&
            active.rect.current.translated &&
            active.rect.current.translated.top >
              over.rect.top + over.rect.height;

          const modifier = isBelowOverItem ? 1 : 0;

          // eslint-disable-next-line prefer-const
          newIndex =
            overIndex >= 0 ? overIndex + modifier : overItems.length + 1;

          recentlyMovedToNewContainer.current = true;
          const updatedItems = {
            ...items,
            [activeContainer]: items[activeContainer].filter(
              (item) => item !== active.id,
            ),
            [overContainer]: [
              ...items[overContainer].slice(0, newIndex),
              items[activeContainer][activeIndex],
              ...items[overContainer].slice(
                newIndex,
                items[overContainer].length,
              ),
            ],
          };
          return updatedItems;
        });
      }
    },
    [items, findContainer],
  );

  const handleDragEnd = useCallback(
    ({ active, over }: DragEndEvent) => {
      const activeContainer = findContainer(active.id);
      if (!over || !activeContainer) {
        setActiveId(null);
        return;
      }

      const { id: activeId } = active;
      const { id: overId } = over;

      const overContainer = findContainer(overId);

      if (!overContainer) {
        setActiveId(null);
        return;
      }

      const activeIndex = items[activeContainer].indexOf(activeId);
      const overIndex = items[overContainer].indexOf(overId);
      setItems((items) => {
        const updatedItems = {
          ...items,
          [overContainer]: arrayMove(
            items[overContainer],
            activeIndex,
            overIndex,
          ),
        };
        const unpinned = updatedItems.unpinned.map((id) => id.toString());
        const left = updatedItems.start.map((id) => id.toString());
        const right = updatedItems.end.map((id) => id.toString());
        // update unpinned order
        onColumnOrderChange(unpinned);
        // update pinned order
        onColumnPinningChange({ left, right });
        return updatedItems;
      });
      setActiveId(null);
    },
    [findContainer, items, onColumnOrderChange, onColumnPinningChange],
  );

  const handleDragCancel = useCallback(() => {
    console.log(itemsBeforeDrag.current);
    setItems({
      start: [...(itemsBeforeDrag.current?.start ?? [])],
      end: [...(itemsBeforeDrag.current?.end ?? [])],
      unpinned: [...(itemsBeforeDrag.current?.unpinned ?? [])],
    });
    itemsBeforeDrag.current = null;
    setActiveId(null);
  }, []);

  const handleReset = () => {
    onReset();
    setItems({
      start: [],
      end: [],
      unpinned: columns.map((col) => col.id || ""),
    });
  };

  // useEffect hook called after a drag operation, to clear the "just moved" status
  useEffect(() => {
    requestAnimationFrame(() => {
      recentlyMovedToNewContainer.current = false;
    });
  }, [items]);

  const hiddenColumnsCount = columns.filter(
    (col) => !col.getIsVisible(),
  ).length;
  const visibleColumnsCount = columns.length - hiddenColumnsCount;
  const draggedItem = columns.find((col) => col.id === activeId);

  return (
    <div>
      <Button
        sx={{
          display: { xs: "none", sm: "flex" },
        }}
        startIcon={<ViewColumnIcon />}
        onClick={() => setOpen(true)}
      >
        Columns
      </Button>
      <Tooltip
        sx={{
          display: { xs: "flex", sm: "none" },
        }}
        title="Customize columns"
        placement="bottom"
      >
        <IconButton color="primary" onClick={() => setOpen(true)}>
          <ViewColumnIcon />
        </IconButton>
      </Tooltip>
      <Drawer
        open={open}
        onClose={() => setOpen(false)}
        anchor="right"
        ModalProps={{ sx: { zIndex: 1300 } }}
      >
        <DndContext
          sensors={sensors}
          modifiers={[restrictToVerticalAxis]}
          collisionDetection={closestCenter}
          onDragStart={handleDragStart}
          onDragOver={handleDragOver}
          onDragEnd={handleDragEnd}
          onDragCancel={handleDragCancel}
          measuring={{
            droppable: {
              strategy: MeasuringStrategy.Always,
            },
          }}
        >
          <Stack
            sx={{
              padding: 2,
              gap: 1,
              minWidth: 400,
            }}
          >
            <Stack
              direction="row"
              sx={{
                alignItems: "center",
                gap: 2,
                justifyContent: "space-between",
              }}
            >
              <Typography variant="h6">Columns</Typography>
              <IconButton onClick={() => setOpen(false)}>
                <Close />
              </IconButton>
            </Stack>
            <Typography variant="caption">
              {hiddenColumnsCount}{" "}
              {hiddenColumnsCount === 1 ? "column" : "columns"} hidden,{" "}
              {visibleColumnsCount}{" "}
              {visibleColumnsCount === 1 ? "column" : "columns"} visible
            </Typography>
            <Card>
              <DroppableArea id="start" items={items.start} columns={columns} />
              <Divider />
              <DroppableArea
                id="unpinned-columns"
                items={items.unpinned}
                columns={columns}
              />
              <Divider />
              <DroppableArea id="end" items={items.end} columns={columns} />
            </Card>
            <Button onClick={handleReset} variant="outlined">
              Reset to default
            </Button>
          </Stack>
          <DragOverlay modifiers={[restrictToWindowEdges]}>
            {draggedItem && activeId ? (
              <ColumnItem column={draggedItem}>
                <DragHandleIcon sx={{ cursor: "grabbing" }} />
              </ColumnItem>
            ) : null}
          </DragOverlay>
        </DndContext>
      </Drawer>
    </div>
  );
};
