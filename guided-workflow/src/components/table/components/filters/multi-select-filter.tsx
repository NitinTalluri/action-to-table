import { Autocomplete, TextField } from "@mui/material";
import { Column } from "@tanstack/react-table";
import { useMemo } from "react";
import { z } from "zod";

import { getHeaderLabel } from "../../utils";

const valueSchema = z.array(z.string());

export const MultiSelectFilter = <T,>({
  column,
  options,
  isFaceted = true,
}: {
  column: Column<T, unknown>;
  options: { value: string; id: string | number | boolean }[];
  isFaceted?: boolean;
}) => {
  const columnFilterValue = column.getFilterValue();
  const getFilterValue = () => {
    const value = valueSchema.safeParse(columnFilterValue);
    return value.success ? value.data : [];
  };
  const header = getHeaderLabel(column);
  const getId = (value?: string | null) => {
    const option = options?.find((option) => option.value === value);
    return option?.id;
  };

  const valueKeys = column.getFacetedUniqueValues().keys();
  const sortedUniqueValues = useMemo(
    () =>
      Array.from(valueKeys)
        .sort()
        .slice(0, 5000)
        .filter((val) => (typeof val === "boolean" ? true : Boolean(val))),
    [valueKeys],
  );

  const getValues = () => {
    return getFilterValue().map((value) => {
      const numberVal = Number(value);
      const booleanVal =
        value === "true" || value === "false" ? value === "true" : undefined;
      const testValue = !isNaN(numberVal) ? numberVal : value;
      return (
        options?.find((option) => {
          if (typeof option.id === "boolean") {
            return option.id === booleanVal;
          }
          const numberOptionId = Number(option.id);
          const typedOptionId = !isNaN(numberOptionId)
            ? numberOptionId
            : option.id;
          return typedOptionId === testValue;
        })?.value || ""
      );
    });
  };
  return (
    <Autocomplete
      disablePortal
      multiple
      id={column.id}
      value={getValues()}
      onChange={(_, values) => {
        const ids = values?.map((value) => String(getId(value)));
        column.setFilterValue(ids.length ? ids : undefined);
      }}
      options={
        options
          ?.filter((option) =>
            isFaceted ? sortedUniqueValues.includes(option.id) : true,
          )
          .map((option) => option.value) || []
      }
      renderInput={(params) => (
        <TextField
          {...params}
          label={
            isFaceted ? `${header} (${sortedUniqueValues.length})` : header
          }
        />
      )}
    />
  );
};
