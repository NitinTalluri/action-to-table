import {
  ColumnFiltersState,
  ColumnPinningState,
  ColumnSizingState,
  ExpandedState,
  SortingState,
  VisibilityState,
} from "@tanstack/react-table";
import { useEffect } from "react";

import useLocalStorage from "~/hooks/useLocalStorage";

export const useTableLocalStorageState = ({
  id,
  defaultColumnOrder,
  initialState,
}: {
  id: string;
  defaultColumnOrder: string[];
  initialState?: Partial<{
    columnFilters: ColumnFiltersState;
    columnVisibility: VisibilityState;
    columnOrder: string[];
    columnSizing: ColumnSizingState;
    columnPinning: ColumnPinningState;
    sorting: SortingState;
  }>;
}) => {
  const [columnSizing, setColumnSizing] = useLocalStorage<ColumnSizingState>({
    key: `${id}-column-sizing`,
    initialValue: initialState?.columnSizing || {},
  });
  const [columnFilters, setColumnFilters] = useLocalStorage<ColumnFiltersState>(
    {
      key: `${id}-column-filters`,
      initialValue: initialState?.columnFilters || [],
    },
  );
  const [sorting, setSorting] = useLocalStorage<SortingState>({
    key: `${id}-sorting`,
    initialValue: initialState?.sorting || [],
  });
  const [expanded, onExpandedChange] = useLocalStorage<ExpandedState>({
    key: `${id}-expanded`,
    initialValue: {},
  });

  // If a column is removed from the table,
  // we need to make sure it is removed from the columnFilters and sorting
  useEffect(() => {
    const sortingIds = sorting.map((sort) => sort.id);
    const columnFilterIds = columnFilters.map((filter) => filter.id);
    const missingColumns = [...sortingIds, ...columnFilterIds].filter(
      (id) => !defaultColumnOrder.includes(id),
    );
    if (missingColumns.length) {
      setColumnFilters((prev) =>
        prev.filter((filter) => !missingColumns.includes(filter.id)),
      );
      setSorting((prev) =>
        prev.filter((sort) => !missingColumns.includes(sort.id)),
      );
    }
  }, [
    columnFilters,
    defaultColumnOrder,
    setColumnFilters,
    setSorting,
    sorting,
  ]);

  const [columnVisibility, setColumnVisibility] =
    useLocalStorage<VisibilityState>({
      key: `${id}-column-visibility`,
      initialValue: initialState?.columnVisibility || {},
    });

  // for column order to work, column definitions must have an id
  const [columnOrder, setColumnOrder] = useLocalStorage<string[]>({
    key: `${id}-column-order`,
    initialValue: initialState?.columnOrder || defaultColumnOrder,
  });
  const [columnPinning, setColumnPinning] = useLocalStorage<ColumnPinningState>(
    {
      key: `${id}-column-pinning`,
      initialValue: initialState?.columnPinning || {},
    },
  );

  // if a new column is added to the table, we need to add it to the columnOrder
  // Otherwise, the new column will not be displayed in the CustomizeColumnsDrawer
  useEffect(() => {
    const allPinnedColumns = Object.values(columnPinning).flat();
    const missingColumns = defaultColumnOrder
      // filter out columns that are already in columnOrder
      .filter((col) => !columnOrder.includes(col))
      // filter out pinned columns
      .filter((col) => !allPinnedColumns.includes(col));

    // if there are missing columns, we must have introduced a new column(s) not previously in the table...
    // ...add these missing columns to the end of the columnOrder
    if (missingColumns.length > 0) {
      setColumnOrder((prev) => [...prev, ...missingColumns]);
    }
  }, [
    columnOrder,
    columnPinning,
    defaultColumnOrder,
    setColumnOrder,
    setColumnPinning,
  ]);

  return {
    state: {
      columnFilters,
      columnVisibility,
      columnOrder,
      columnSizing,
      columnPinning,
      sorting,
      expanded,
    },
    onColumnFiltersChange: setColumnFilters,
    onColumnVisibilityChange: setColumnVisibility,
    onColumnOrderChange: setColumnOrder,
    onColumnSizingChange: setColumnSizing,
    onColumnPinningChange: setColumnPinning,
    onSortingChange: setSorting,
    onExpandedChange,
  };
};
