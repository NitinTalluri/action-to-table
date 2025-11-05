import ArrowForwardIos from "@mui/icons-material/ArrowForwardIos";
import Check from "@mui/icons-material/Check";
import {
  Button,
  Chip,
  Divider,
  ListItemIcon,
  ListItemText,
  ListSubheader,
  MenuItem,
  MenuList,
  Paper,
  Popover,
} from "@mui/material";
import { MouseEvent, useState } from "react";

import {
  categoryTotals,
  dateFilters,
  dateTotals,
  RenderTree,
  TFilters,
  viewFilters,
} from "./utils";

export const FilterSelect = ({
  dc_user_id,
  treeConfig,
  filters,
  onChange,
}: {
  dc_user_id?: number;
  treeConfig: RenderTree[];
  filters: TFilters;
  onChange: (newFilters: TFilters) => void;
}) => {
  const [anchorEl, setAnchorEl] = useState<HTMLButtonElement | null>(null);

  const handleClick = (event: MouseEvent<HTMLButtonElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  const open = Boolean(anchorEl);
  const id = open ? "filters-popover" : undefined;

  const { last_24_hours, last_hour, last_month, last_week } = dateTotals(
    treeConfig,
    filters.view,
    dc_user_id,
  );
  const { error, result, task, pending } = categoryTotals(
    treeConfig,
    filters.dates,
    filters.view,
    dc_user_id,
  );

  const handleFilterCategoryChange = (filter: TFilters["category"][number]) => {
    if (filters.category.includes(filter)) {
      onChange({
        ...filters,
        category: filters.category.filter((c) => c !== filter),
      });
    } else {
      onChange({ ...filters, category: [...filters.category, filter] });
    }
  };

  const handleDateChange = (rangeString: TFilters["dates"]) => {
    if (filters.dates === rangeString) {
      onChange({ ...filters, dates: "" });
      return;
    }
    onChange({
      ...filters,
      dates: rangeString,
    });
  };

  const handleViewChange = (viewString: TFilters["view"]) => {
    if (filters.view === viewString) {
      onChange({ ...filters, view: "" });
      return;
    }
    onChange({
      ...filters,
      view: viewString,
    });
  };

  return (
    <>
      <Button
        fullWidth
        variant="outlined"
        sx={{ justifyContent: "space-between" }}
        endIcon={<ArrowForwardIos />}
        onClick={handleClick}
      >
        Filter Selection
      </Button>
      <Popover
        id={id}
        open={open}
        anchorEl={anchorEl}
        onClose={handleClose}
        anchorOrigin={{
          vertical: "top",
          horizontal: "right",
        }}
      >
        <Paper sx={{ width: 320, maxWidth: "100%" }}>
          <MenuList dense subheader={<ListSubheader>View</ListSubheader>}>
            <MenuItem onClick={() => handleViewChange(viewFilters[0])}>
              <ListItemIcon>
                {filters.view === viewFilters[0] ? <Check /> : null}
              </ListItemIcon>
              <ListItemText>All Users</ListItemText>
            </MenuItem>
          </MenuList>
          <Divider />

          <MenuList dense subheader={<ListSubheader>Date range</ListSubheader>}>
            <MenuItem onClick={() => handleDateChange(dateFilters[0])}>
              <ListItemIcon>
                {filters.dates === dateFilters[0] ? <Check /> : null}
              </ListItemIcon>
              <ListItemText>Last hour</ListItemText>
              <Chip label={last_hour} />
            </MenuItem>
            <MenuItem onClick={() => handleDateChange(dateFilters[1])}>
              <ListItemIcon>
                {filters.dates === dateFilters[1] ? <Check /> : null}
              </ListItemIcon>
              <ListItemText>Last 24 hours</ListItemText>
              <Chip label={last_24_hours} />
            </MenuItem>
            <MenuItem onClick={() => handleDateChange(dateFilters[2])}>
              <ListItemIcon>
                {filters.dates === dateFilters[2] ? <Check /> : null}
              </ListItemIcon>
              <ListItemText>Last week</ListItemText>
              <Chip label={last_week} />
            </MenuItem>
            <MenuItem onClick={() => handleDateChange(dateFilters[3])}>
              <ListItemIcon>
                {filters.dates === dateFilters[3] ? <Check /> : null}
              </ListItemIcon>
              <ListItemText>Last month</ListItemText>
              <Chip label={last_month} />
            </MenuItem>
          </MenuList>
          <Divider />

          <MenuList dense subheader={<ListSubheader>Category</ListSubheader>}>
            <MenuItem onClick={() => handleFilterCategoryChange("pending")}>
              <ListItemIcon>
                {filters.category.includes("pending") ? <Check /> : null}
              </ListItemIcon>
              <ListItemText>Pending</ListItemText>
              <Chip label={pending} color="info" />
            </MenuItem>
            <MenuItem onClick={() => handleFilterCategoryChange("error")}>
              <ListItemIcon>
                {filters.category.includes("error") ? <Check /> : null}
              </ListItemIcon>
              <ListItemText>Errors</ListItemText>
              <Chip label={error} color="error" />
            </MenuItem>
            <MenuItem onClick={() => handleFilterCategoryChange("task")}>
              <ListItemIcon>
                {filters.category.includes("task") ? <Check /> : null}
              </ListItemIcon>
              <ListItemText>Tasks</ListItemText>
              <Chip label={task} color="warning" />
            </MenuItem>
            <MenuItem onClick={() => handleFilterCategoryChange("result")}>
              <ListItemIcon>
                {filters.category.includes("result") ? <Check /> : null}
              </ListItemIcon>
              <ListItemText>Results</ListItemText>
              <Chip label={result} color="success" />
            </MenuItem>
          </MenuList>
          <Divider />
        </Paper>
      </Popover>
    </>
  );
};
