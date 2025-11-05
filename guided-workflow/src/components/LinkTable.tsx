import {
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Paper,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TableSortLabel,
  Typography,
} from "@mui/material";
import { createColumnHelper, flexRender } from "@tanstack/react-table";
import { useMemo, useState } from "react";

import { TLink } from "~/domain/Engagement";

import { DialogCloseButton } from "./Dialog";
import { SortIndicator } from "./table/components/sort-indicator";
import { useTypedTable } from "./table/hooks";
import { useTableLocalStorageState } from "./table/hooks/use-table-local-storage-state";

type TLinkTableProps = {
  links: TLink[];
  title: string;
  onDelete: (link: TLink) => void;
};

const columnHelper = createColumnHelper<TLink>();

const columns = (onDelete: (link: TLink) => void) => [
  columnHelper.accessor("id", {
    id: "id",
    header: "ID",
  }),
  columnHelper.accessor("id", {
    id: "actions",
    header: "Actions",
    cell: (info) => (
      <ActionsCell onDelete={() => onDelete(info.row.original)} />
    ),
    size: 100,
    enableSorting: false,
  }),
];

const LinkTable = (props: TLinkTableProps) => {
  const { links, title, onDelete } = props;
  const linkType = links?.[0]?.link_type;

  const {
    state: { sorting },
    onSortingChange,
  } = useTableLocalStorageState({
    id: `link-table-${linkType}`,
    defaultColumnOrder: ["id", "actions"],
  });

  const table = useTypedTable({
    data: links,
    columns: useMemo(() => columns(onDelete), [onDelete]),
    state: { sorting },
    onSortingChange,
  });

  return (
    <Stack>
      <Typography variant="h6">{title}</Typography>
      <TableContainer component={Paper}>
        <Table size="small">
          <TableHead>
            {table.getHeaderGroups().map((headerGroup) => (
              <TableRow key={headerGroup.id}>
                {headerGroup.headers.map((header) => {
                  const isMultiSorting = table.getState().sorting.length > 1;
                  const isSorted = header.column.getIsSorted();
                  const sortIndex = table
                    .getState()
                    .sorting.findIndex((sort) => sort.id === header.column.id);
                  const sortDirection =
                    isSorted === "asc"
                      ? "asc"
                      : isSorted === "desc"
                        ? "desc"
                        : undefined;

                  return (
                    <TableCell
                      key={header.id}
                      style={{ width: header.getSize() }}
                    >
                      <TableSortLabel
                        active={Boolean(sortDirection)}
                        direction={sortDirection || undefined}
                        onClick={header.column.getToggleSortingHandler()}
                      >
                        {flexRender(
                          header.column.columnDef.header,
                          header.getContext(),
                        )}
                        {isMultiSorting && sortDirection && isSorted ? (
                          <SortIndicator index={sortIndex} />
                        ) : null}
                      </TableSortLabel>
                    </TableCell>
                  );
                })}
              </TableRow>
            ))}
          </TableHead>
          <TableBody>
            {table.getRowModel().rows.map((row) => (
              <TableRow key={row.id}>
                {row.getVisibleCells().map((cell) => (
                  <TableCell
                    key={cell.id}
                    style={{ width: cell.column.getSize() }}
                  >
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </TableCell>
                ))}
              </TableRow>
            ))}
          </TableBody>
        </Table>
        {links.length === 0 ? (
          <Box
            sx={{
              padding: 2,
            }}
          >
            <Typography
              align="center"
              sx={{
                color: "textSecondary",
              }}
            >
              No data available
            </Typography>
          </Box>
        ) : null}
      </TableContainer>
    </Stack>
  );
};

export default LinkTable;

const ActionsCell = ({ onDelete }: { onDelete: () => void }) => {
  const [open, setOpen] = useState(false);
  return (
    <div>
      <Button color="error" onClick={() => setOpen(true)}>
        Delete
      </Button>
      <Dialog open={open} onClose={() => setOpen(false)} fullWidth>
        <DialogTitle>Delete Link?</DialogTitle>
        <DialogCloseButton handleClose={() => setOpen(false)} />
        <DialogContent>
          <Typography>
            Are you sure you want to delete this link? This is a permanent
            action and cannot be undone.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpen(false)}>Cancel</Button>
          <Button
            color="error"
            variant="outlined"
            onClick={() => {
              onDelete();
              setOpen(false);
            }}
          >
            Delete
          </Button>
        </DialogActions>
      </Dialog>
    </div>
  );
};
