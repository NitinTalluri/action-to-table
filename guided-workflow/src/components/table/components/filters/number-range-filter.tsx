import Close from "@mui/icons-material/Close";
import { FormLabel, IconButton, Stack, TextField } from "@mui/material";
import { Column } from "@tanstack/react-table";
import { z } from "zod";

import { getHeaderLabel } from "../../utils";

const rangeSchema = z.tuple([z.number().nullish(), z.number().nullish()]);
const getRange = <T,>(column: Column<T, unknown>) => {
  const parsed = rangeSchema.safeParse(column.getFilterValue());
  if (parsed.success) return parsed.data;
  return undefined;
};

export const NumberRangeFilter = <T,>({
  column,
}: {
  column: Column<T, unknown>;
}) => {
  const header = getHeaderLabel(column);
  const rangeVal = getRange(column);
  const getConstraintValue = (position: 0 | 1) => {
    const maxValue = column.getFacetedMinMaxValues()?.[position];
    if (typeof maxValue === "number") return maxValue;
    if (Array.isArray(maxValue)) return maxValue?.[0];
    return undefined;
  };
  return (
    <Stack
      sx={{
        gap: 1,
      }}
    >
      <Stack
        direction="row"
        sx={{
          gap: 2,
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <FormLabel>{header}</FormLabel>
        {rangeVal ? (
          <IconButton size="small" onClick={() => column.setFilterValue(null)}>
            <Close />
          </IconButton>
        ) : null}
      </Stack>
      <Stack
        direction="row"
        sx={{
          gap: 1,
        }}
      >
        <TextField
          fullWidth
          label="Min"
          type="number"
          value={rangeVal?.[0] ?? ""}
          onChange={(e) =>
            column.setFilterValue((old: [number, number]) => [
              Number(e.target.value),
              old?.[1],
            ])
          }
          placeholder={`Min (${getConstraintValue(0) || "0"})`}
          slotProps={{
            input: {
              inputProps: {
                min: getConstraintValue(0),
                max: getConstraintValue(1),
              },
            },
          }}
        />
        <TextField
          fullWidth
          label="Max"
          type="number"
          value={rangeVal?.[1] ?? ""}
          onChange={(e) =>
            column.setFilterValue((old: [number, number]) => [
              old?.[0],
              Number(e.target.value),
            ])
          }
          placeholder={`Max (${getConstraintValue(1) || ""})`}
          slotProps={{
            input: {
              inputProps: {
                min: getConstraintValue(0),
                max: getConstraintValue(1),
              },
            },
          }}
        />
      </Stack>
    </Stack>
  );
};
