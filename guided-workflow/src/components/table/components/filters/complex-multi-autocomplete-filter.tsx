import { Autocomplete, TextField } from "@mui/material";
import { Column } from "@tanstack/react-table";
import { useMemo } from "react";
import { z } from "zod";

import { getHeaderLabel } from "../../utils";

const valueSchema = z.array(z.string());

// Best used when attempting to filter a column whose values are complex arrays
// (e.g. objects or arrays of objects)
export const ComplexMultiAutocompleteFilter = <T,>({
  column,
  getOptions,
}: {
  column: Column<T>;
  getOptions: (values: unknown) => string[];
}) => {
  const getFilterValue = () => {
    const value = valueSchema.safeParse(column.getFilterValue());
    return value.success ? value.data : [];
  };
  const header = getHeaderLabel(column);

  const sortedUniqueValues = useMemo(
    () =>
      Array.from(column.getFacetedUniqueValues().keys()).sort().slice(0, 5000),
    [column],
  );

  const getParsedUniqueValues = useMemo(
    () => getOptions(sortedUniqueValues),
    [sortedUniqueValues, getOptions],
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
      options={getParsedUniqueValues}
      getOptionLabel={(option) => String(option)}
      renderInput={(params) => (
        <TextField
          {...params}
          label={`${header} (${getParsedUniqueValues.length})`}
        />
      )}
    />
  );
};
