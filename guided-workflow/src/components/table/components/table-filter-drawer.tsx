import Close from "@mui/icons-material/Close";
import FilterListIcon from "@mui/icons-material/FilterList";
import {
  Box,
  Button,
  Drawer,
  IconButton,
  Stack,
  Tooltip,
  Typography,
} from "@mui/material";
import { Column, HeaderGroup } from "@tanstack/react-table";
import React, { useState } from "react";

export const TableFiltersDrawer = <T,>({
  headers,
  filterCount,
  totalCount,
  onClear,
  label,
  children,
}: {
  onClear: () => void;
  filterCount: number;
  totalCount: number;
  headers: HeaderGroup<T>[];
  label: string;
  children: (props: {
    column: Column<T, unknown>;
    key: string;
  }) => React.ReactNode;
}) => {
  const [open, setOpen] = useState(false);

  return (
    <div>
      <Button
        sx={{
          display: { xs: "none", sm: "flex" },
        }}
        startIcon={<FilterListIcon />}
        onClick={() => setOpen(true)}
      >
        Filters {filterCount ? `(${filterCount})` : null}
      </Button>
      <Box sx={{ position: "relative" }}>
        <Tooltip
          sx={{
            display: { xs: "flex", sm: "none" },
          }}
          title="Filters"
          placement="bottom"
        >
          <IconButton color="primary" onClick={() => setOpen(true)}>
            <FilterListIcon />
          </IconButton>
        </Tooltip>
        {filterCount > 0 ? (
          <Box
            sx={(theme) => ({
              display: { xs: "flex", sm: "none" },
              position: "absolute",
              width: 7.5,
              height: 7.5,
              background: theme.palette.primary.main,
              borderRadius: "50%",
              top: 2.5,
              right: 2.5,
            })}
          />
        ) : null}
      </Box>
      <Drawer
        open={open}
        onClose={() => setOpen(false)}
        anchor="right"
        ModalProps={{
          sx: {
            zIndex: 1300,
          },
        }}
      >
        <Stack
          direction="row"
          sx={[
            {
              alignItems: "center",
              gap: 2,
              justifyContent: "space-between",
            },
            (theme) => ({
              position: "sticky",
              top: 0,
              background: theme.palette.background.paper,
              zIndex: 2,
              padding: 2,
              borderBottom: `1px solid ${theme.palette.divider}`,
            }),
          ]}
        >
          <Stack>
            <Typography variant="h6">Filters</Typography>
            <Typography variant="caption">
              {totalCount} {label} found
            </Typography>
          </Stack>
          <IconButton onClick={() => setOpen(false)}>
            <Close />
          </IconButton>
        </Stack>
        <Stack
          sx={{
            padding: 2,
            gap: 2,
            minWidth: 400,
            maxWidth: 600,
          }}
        >
          {headers.map((headerGroup) => (
            <Stack
              key={headerGroup.id}
              sx={{
                gap: 2,
              }}
            >
              {headerGroup.headers.map((header) => {
                if (!header.column.getCanFilter()) return null;
                return children({ column: header.column, key: header.id });
              })}
            </Stack>
          ))}
        </Stack>
        <Stack
          sx={(theme) => ({
            position: "sticky",
            bottom: 0,
            background: theme.palette.background.paper,
            zIndex: 2,
            padding: 2,
            borderTop: `1px solid ${theme.palette.divider}`,
          })}
        >
          <Button disabled={!filterCount} variant="outlined" onClick={onClear}>
            Clear Filters {filterCount ? `(${filterCount})` : null}
          </Button>
        </Stack>
      </Drawer>
    </div>
  );
};
