# Tables

This is an outline for our approach to data display, filtering, and sorting when using tables within the app. We currently use `@tanstack/react-table` for table creation. For more information and examples of `@tanstack/react-table`, [check out their docs](https://tanstack.com/table/latest) and be sure to select the version that corresponds with the version found in our `package.json`.

---

### Table of contents

- [Columns](#columns)
- [Hooks](#hooks)
- [Table state](#table-state)
- [Filtering](#filtering)
- [Column Customization](#column-customization)
- [All Together](#all-together)

## Columns

Much of the table is controlled via the column definition. This includes column header text/functionality, how the cell is rendered, the sizing of the column, if it should be sortable, and much more. Our preferred method of creating column definitions is with a `createColumnHelper`.

```ts
import { createColumnHelper } from "@tanstack/react-table";
import { TData } from "../data-type";

const columnHelper = createColumnHelper<TData>();
```

The `columnHelper` object can then be used to create type-safe columns.

```ts
export const columns = [
  columnHelper.accessor("start_date", {
    id: "start_date", // the id is needed for column reordering
    header: "Start Date", // displayed in the header row
    cell: (info) => info.getValue(), // this cell will simple render the value passed to it
    filterFn: "dateBetweenFilterFn", // a filterFn dictates how the table should filter the cell value
    minSize: 175, // the min width of this column
    size: 250, // the default width of this column
    maxSize: 400, // the max width of this column
    enableColumnFilter: false, // true by default
  }),
];
```

---

## Hooks

A table can be built with either `tanstack`'s default `useReactTable` hook or with one of our more pre-configured and feature rich hooks.

- `useTypedTable`: a thin cover around `useReactTable` that has built in custom `filterFns` along with some basic defaults. This hook would be useful when setting up a simple table that doesn't need much in terms of user editable column customization.
- `useFacetedTable`: a more robust filter that enables multisort and faceted filtering. This hook is generally recommended as the go to table hook.

```ts
import { useFacetedTable } from "~/components/table/hooks/use-faceted-table";

const table = useFacetedFilter({
  data,
  columns,
});
```

Each of these hooks can be expanded and customized as the specific table needs.

## Table State

Table state by default is handled internally by the table hook, but it can also be handled externally. This can be useful if we want to chain a side-effect with some table specific state change. For example, we might want to save the table's column sort to local storage so the user can return to the table with it pre-sorted.

We have a useful hook to handle local-storage specific table state. Otherwise, a simple `useState` hook will work.

```ts
import { useTableLocalStorageState } from "~/components/table/hooks/use-table-local-storage-state";
import { useFacetedTable } from "~/components/table/hooks/use-faceted-table";

const {
  state,
  onColumnFiltersChange,
  onColumnOrderChange,
  onColumnSizingChange,
  onColumnVisibilityChange,
  onColumnPinningChange,
  onSortingChange,
} = useTableLocalStorageState({
  id: "unique-table-id", // this must be a unique indentifier to avoid conflicts with other tables
  defaultColumnOrder: columns.map((col) => col.id || ""),
});

// the state and setters are then fed to the useFacetedTable hook
const table = useFacetedTable({
  data,
  columns,
  state,
  onColumnFiltersChange,
  onColumnVisibilityChange,
  onColumnOrderChange,
  onColumnSizingChange,
  onColumnPinningChange,
  onSortingChange,
});
```

## Components

We have a handful of custom table components. Most of them are build upon MUI components. If one of our custom components does not meet your needs during development, it is preferred that you make a custom table using the MUI components as opposed to introducing large updates to our default components without first running the proposed update(s) by the rest of the dev team.

- `TablePagination`: displays the table's available pages along with forward and backwards buttons. Allows for page size to be updated by user. Devs can pass in an array of custom page sizes if needed.
  _Note: Table pagination requires `getPaginationRowModel: getPaginationRowModel(),` to be added to the table setup hook (`useReactTable` etc)_
- `TableDragHandle`: should be used within a table column's header. Allows the user to click and drag to increase/decrease the width of a column
- `SortIndicator`: Used in the header cell to indicate the current sort order if the table is setup to allow multi column sort
- `EditableCell`: A simple editable cell that can update different data types via the `variant` prop.
  _Note: In order for cell updates to save, the table's setup hook must include the following:_

```ts
useReactTable({
  ...
  meta: {
    updateData: (rowIndex: number, columnId: string, value: unknown) => {
      // your custom update function
      // This could update a react query data store, local state, etc
    },
  },
  ...
});
```

- `ClickableTableRow`: a basic table row that takes an `onClick` function if something specific like routing should happen when a user clicks a row.
  _Note: This should not be used if the table includes checkboxes for multi-row select_
- `VirtualizedTable`: This is the most complete "out of the box" solution for full featured table functionality. It is best paired with the `useFacetedTable` hook, but can be used with any flavor of table setup hook. This table utilizes the `@tanstack/react-virtual` to handle large row counts via virtualization. Using this component also allows for column resizing. An optional `renderRow` prop can be passed if the table should have custom row functionality (as seen in the example below)

```tsx
<VirtualizedTable
  table={table}
  renderRow={(props) => (
    <ClickableRow
      key={props.row.id}
      {...props}
      onClick={() => onSelect(props.row.original)}
      isSelected={selectedRow === props.row.original.id}
    />
  )}
/>
```

## Filtering

Filtering is handled via the column definition and then must be displayed in the UI either with a custom component or by using our `TableFiltersDrawer` and `TableFilters`.

Tanstack-table comes with several default `filterFns` that can be specified in the column definition. If none of the built in functions work for your data, you may write a custom function.

```ts
columnHelper.accessor("booking_contract", {
  id: "booking_contract",
  header: "Contract",
  cell: (info) => info.getValue(),
  filterFn: "equals", // read the docs for more info on what each filterFn does
  minSize: 100,
}),
```

```tsx
<TableFiltersDrawer
  label="my items"
  headers={table.getHeaderGroups()}
  totalCount={table.getRowCount()}
  // can come from the `useTableLocalStorageState` or any state accessible to this component
  onClear={() => onColumnFiltersChange([])}
  filterCount={state.columnFilters.length}
>
  {(props) => (
    <TableFilters
      {...props}
      // selectOptions are used for dropdowns that need key value pairs to display human readable text
      selectOptions={{
        // keys must correspond to column id
        buying_program_type_id: buying_program_options,
        sold_as_service_type_id: service_type_options,
        sold_as_pricing_type_id: pricing_model_options,
      }}
    />
  )}
</TableFiltersDrawer>
```

The `TableFiltersDrawer` component will map over the table's headers provided via the `headers` prop and will render a child if the header has filtering enabled (controlled within the `columns` definition). This component then uses render props to render children. This means you can use our default `TableFilters` component or write your own custom component if your data requires it.

The `TableFilters` component will render a different filter based on the column's `meta` object. **This is extremely important:** When defining your column, consider what UI will be required to render its filter, then add the corresponding string to the meta object.

Example:

```ts
columnHelper.accessor("agreement_end_date", {
  id: "agreement_end_date",
  header: "End Date",
  cell: (info) => new Date(info.getValue() + `T00:00:00`).toDateString(),
  filterFn: "dateBetweenFilterFn",
  meta: {
    filterVariant: TableMetaEnums.Enum.date, // the TableFilters component will parse the meta object to grab the filterVariant and then render the correct UI
  },
}),
```

## Column Customization

In many situations we may want to give the user the ability to update the layout of the table in question. A user may want to hide columns they deem unnecessary to the experience and/or reorder columns so that data appears in an order that makes more sense to them. This can be solved by passing `columnOrder`, `columnVisibility` and `columnPinning` state (along with their setter functions) to your table hook.

```ts
const [columnVisibility, setColumnVisibility] = useState<VisibilityState>({});
// ! for column order to work, column definitions must have an id
const [columnOrder, setColumnOrder] = useState<string[]>([]);
const [columnPinning, setColumnPinning] = useState<ColumnPinningState>({});

const table = useFacetedTable({
  data,
  columns,
  state: {
    columnVisibility,
    columnOrder,
    columnPinning,
  },
  onColumnVisibilityChange,
  onColumnOrderChange,
  onColumnPinningChange,
});
```

The `CustomizeColumnsDrawer` can then be used to display a drag-and-drop experience for users to reorder, pin, and show/hide their columns.

```tsx
<CustomizeColumnsDrawer
  columns={table.getAllFlatColumns()}
  columnOrder={state.columnOrder}
  onColumnOrderChange={onColumnOrderChange}
  onColumnPinningChange={onColumnPinningChange}
  onReset={() => {
    onColumnOrderChange([]);
    onColumnVisibilityChange({});
    onColumnPinningChange({});
  }}
/>
```

## All Together

When using some or all of these components and hooks together, it is possible to create a feature rich table with minimal boilerplate while still allowing for deep customization if required.

```ts
// Create column definitions
const columnHelper = createColumnHelper<TData>();

const columns = [
  columnHelper.accessor("start_date", {
    id: "start_date", // the id is needed for column reordering
    header: "Start Date",
    cell: (info) => info.getValue(),
    filterFn: "dateBetweenFilterFn", // a filterFn dictates how the table should filter the cell value
    meta: {
      filterVariant: TableMetaEnums.Enum.date // dictates the filter UI
    }
  }),
]

const MyTable = ({data}: {data: TData[]}) => {
  // use local storage table hook to track table state in local storage for better UX
  const {
    state,
    onColumnFiltersChange,
    onColumnOrderChange,
    onColumnSizingChange,
    onColumnVisibilityChange,
    onColumnPinningChange,
    onSortingChange,
  } = useTableLocalStorageState({
    id: "my-unique-table",
    defaultColumnOrder: columns.map((col) => col.id || ""),
  });

  // pass data, columns, and state to table hook
  const table = useFacetedTable({
    data,
    columns,
    state,
    onColumnFiltersChange,
    onColumnVisibilityChange,
    onColumnOrderChange,
    onColumnSizingChange,
    onColumnPinningChange,
    onSortingChange,
  });

  return (
    <Stack gap={1}>
      {/* Column Customization and Filtering */}
      <Stack direction="row" gap={1} justifyContent="end">
        <CustomizeColumnsDrawer
          columns={table.getAllFlatColumns()}
          columnOrder={state.columnOrder}
          onColumnOrderChange={onColumnOrderChange}
          onColumnPinningChange={onColumnPinningChange}
          onReset={() => {
            onColumnOrderChange(columns.map((col) => col.id || ""));
            onColumnVisibilityChange({});
            onColumnPinningChange({});
          }}
        />
        <TableFiltersDrawer
          label="items"
          headers={table.getHeaderGroups()}
          totalCount={table.getRowCount()}
          onClear={() => onColumnFiltersChange([])}
          filterCount={state.columnFilters.length}
        >
          {(props) => (
            <TableFilters
              {...props}
              selectOptions={{}}
            />
          )}
        </TableFiltersDrawer>
      </Stack>
      {/* The actual table render */}
      <VirtualizedTable
        table={table}
        renderRow={(props) => (
          <ClickableRow
            key={props.row.id}
            {...props}
            onClick={() => navigate(props.row.original)}
          />
        )}
      />
    </Stack>
  )
}

```
