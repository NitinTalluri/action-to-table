import { Box, capitalize, Chip, Typography } from "@mui/material";

import { isCategory, isDate, isView, TFilters } from "./utils";

export const Readback = ({
  filters,
  onChange,
}: {
  filters: TFilters;
  onChange: (newFilters: TFilters) => void;
}) => {
  const handleRemoveFilter = (
    value: TFilters["category"][number] | TFilters["dates"] | TFilters["view"],
  ) => {
    if (isCategory(value)) {
      onChange({
        ...filters,
        category: filters.category.filter((t) => t !== value),
      });
    }
    if (isDate(value)) {
      onChange({ ...filters, dates: "" });
    }
    if (isView(value)) {
      onChange({ ...filters, view: "" });
    }
  };

  const handleRemoveAll = () => {
    onChange({ category: [], dates: "", view: "" });
  };

  const totalFiltersApplied =
    filters.category.length + (filters.dates ? 1 : 0) + (filters.view ? 1 : 0);

  return (
    <Box
      sx={{
        display: "flex",
        alignItems: "center",
        flexWrap: "wrap",
        gap: 1,
        minHeight: "48px",
      }}
    >
      {totalFiltersApplied === 0 ? (
        <Typography sx={{ margin: 0, color: "grey.600" }}>
          No filters applied
        </Typography>
      ) : null}

      {filters.view ? (
        <Chip
          label={capitalize(filters.view).split("_").join(" ")}
          onDelete={() => handleRemoveFilter(filters.view)}
        />
      ) : null}

      {filters.dates ? (
        <Chip
          label={capitalize(filters.dates).split("_").join(" ")}
          onDelete={() => handleRemoveFilter(filters.dates)}
        />
      ) : null}

      {filters.category.map((filter) => (
        <Chip
          key={filter}
          label={capitalize(filter)}
          onDelete={() => handleRemoveFilter(filter)}
        />
      ))}
      {totalFiltersApplied > 1 ? (
        <Chip label="Remove all filters" onDelete={handleRemoveAll} />
      ) : null}
    </Box>
  );
};
