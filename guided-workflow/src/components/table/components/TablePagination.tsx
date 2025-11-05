import {
  FormControl,
  InputLabel,
  MenuItem,
  Pagination,
  Select,
  Stack,
} from "@mui/material";
import { Table } from "@tanstack/react-table";

const DEFAULT_PAGE_SIZES = [5, 10, 15, 20];

export const TablePagination = <T,>({
  table,
  pageSizes = DEFAULT_PAGE_SIZES,
}: {
  table: Table<T>;
  pageSizes?: number[];
}) => {
  const currentPageSize = table.getState().pagination.pageSize;
  const totalPages = table.getPageCount();
  const currentPage = table.getState().pagination.pageIndex + 1;
  return (
    <Stack
      direction="row"
      spacing={1}
      sx={{
        justifyContent: "end",
        position: "sticky",
        bottom: 0,
        bgcolor: "white",
        padding: ".5rem",
      }}
    >
      <Pagination
        count={totalPages}
        page={currentPage}
        onChange={(e, page) => table.setPageIndex(page - 1)}
      />
      <FormControl>
        <InputLabel id="demo-simple-select-label">Page Size</InputLabel>
        <Select
          label="Page Size"
          value={currentPageSize}
          onChange={(e) => table.setPageSize(Number(e.target.value))}
          sx={{
            minWidth: "5rem",
          }}
        >
          {pageSizes.map((pageSize) => (
            <MenuItem key={pageSize} value={pageSize}>
              {pageSize}
            </MenuItem>
          ))}
        </Select>
      </FormControl>
    </Stack>
  );
};
