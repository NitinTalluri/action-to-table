import { Autocomplete, TextField } from "@mui/material";
import { Column } from "@tanstack/react-table";
import { useMemo } from "react";

import { getHeaderLabel } from "../../utils";

export const SelectFilter = <T,>({
  column,
  options,
}: {
  column: Column<T, unknown>;
  options: { value: string; id: string | number | boolean }[];
}) => {
  const columnFilterValue = column.getFilterValue();
  const header = getHeaderLabel(column);
  const getId = (value?: string | null) => {
    const option = options?.find((option) => option.value === value);
    return option?.id;
  };

  const valueKeys = column.getFacetedUniqueValues().keys();
  const sortedUniqueValues = useMemo(
    () => Array.from(valueKeys).sort().slice(0, 5000).filter(Boolean),
    [valueKeys],
  );

  const getValue = () => {
    const numberVal = Number(columnFilterValue);
    const testValue = !isNaN(numberVal) ? numberVal : columnFilterValue;
    return options?.find((option) => option.id === testValue)?.value || "";
  };
  return (
    <Autocomplete
      disablePortal
      id={column.id}
      value={getValue()}
      onChange={(_, value) => {
        if (getId(value)) {
          // react table seems to want this val as a string for the search func
          column.setFilterValue(String(getId(value)));
        } else {
          column.setFilterValue(null);
        }
      }}
      options={
        options
          ?.filter((option) => sortedUniqueValues.includes(option.id))
          .map((option) => option.value) || []
      }
      renderInput={(params) => (
        <TextField
          {...params}
          label={`${header} (${sortedUniqueValues.length})`}
        />
      )}
    />
  );
};
