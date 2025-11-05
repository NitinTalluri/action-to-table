import { Autocomplete, TextField } from "@mui/material";
import { Column } from "@tanstack/react-table";
import { useMemo } from "react";
import { z } from "zod";

import { getHeaderLabel } from "../../utils";

const valueSchema = z.array(z.union([z.string(), z.number()]));

export const MultiAutocompleteFilter = <T,>({
  column,
}: {
  column: Column<T, unknown>;
}) => {
  const columnFilterValue = column.getFilterValue();
  const getFilterValue = () => {
    const value = valueSchema.safeParse(columnFilterValue);
    return value.success ? value.data : [];
  };
  const header = getHeaderLabel(column);

  const valueKeys = column.getFacetedUniqueValues().keys();
  const sortedUniqueValues = useMemo(
    () => Array.from(valueKeys).sort().slice(0, 5000).filter(Boolean),
    [valueKeys],
  );

  return (
    <Autocomplete
      disablePortal
      multiple
      id={column.id}
      value={getFilterValue()}
      onChange={(_, value) =>
        column.setFilterValue(value?.length ? value : undefined)
      }
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
