import { Autocomplete, TextField } from "@mui/material";
import { Column } from "@tanstack/react-table";
import { useMemo } from "react";

import { getHeaderLabel } from "../../utils";

export const AutocompleteFilter = <T,>({
  column,
}: {
  column: Column<T, unknown>;
}) => {
  const columnFilterValue = column.getFilterValue();
  const header = getHeaderLabel(column);

  const valueKeys = column.getFacetedUniqueValues().keys();
  const sortedUniqueValues = useMemo(
    () => Array.from(valueKeys).sort().slice(0, 5000).filter(Boolean),
    [valueKeys],
  );
  return (
    <Autocomplete
      disablePortal
      id={column.id}
      value={columnFilterValue ? String(columnFilterValue) : ""}
      isOptionEqualToValue={(option, value) => option.id === value.id}
      onChange={(_, value) => column.setFilterValue(value)}
      options={sortedUniqueValues}
      getOptionLabel={(option) => String(option)}
      renderInput={(params) => (
        <TextField
          {...params}
          label={`${header} (${sortedUniqueValues.length})`}
        />
      )}
    />
  );
};
