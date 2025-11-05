import Close from "@mui/icons-material/Close";
import { Button, FormHelperText, FormLabel, Stack } from "@mui/material";
import {
  DatePicker,
  DateValidationError,
  LocalizationProvider,
} from "@mui/x-date-pickers";
import { AdapterDateFns } from "@mui/x-date-pickers/AdapterDateFns";
import { Column } from "@tanstack/react-table";
import { useState } from "react";

import { getHeaderLabel } from "../../utils";
import {
  formatDateToYYYYMMDD,
  getDateFilterVal,
  getLargerDate,
  getLowerDate,
  isValidDateString,
} from "./utils";

// removing the time part of the date-time string for easier logic
const splitDateFromDateTime = (dateTimeStr: string) => {
  return dateTimeStr.split("T")[0];
};

export const DateRangeFilter = <T,>({
  column,
}: {
  column: Column<T, unknown>;
}) => {
  const minMax = column.getFacetedMinMaxValues();
  const columnFilterValue = column.getFilterValue();
  const getMinMax = (pos: 0 | 1) => {
    if (!minMax) return null;
    if (!Array.isArray(minMax) || minMax.length !== 2) return null;
    const minVal = minMax[pos];
    if (typeof minVal === "string") return splitDateFromDateTime(minVal);
    if (Array.isArray(minVal) && typeof minVal[0] === "string") {
      return splitDateFromDateTime(minVal[0]);
    }
  };
  const min = getMinMax(0);
  const max = getMinMax(1);
  const dateValues = getDateFilterVal(columnFilterValue);

  const header = getHeaderLabel(column);

  const hasDateValues = dateValues?.some((v) => v !== undefined);
  const greatestMin = getLargerDate(min, dateValues?.[0]);
  const smallestMax = getLowerDate(max, dateValues?.[1]);

  const [minError, setMinError] = useState<DateValidationError>(null);
  const [maxError, setMaxError] = useState<DateValidationError>(null);

  return (
    <Stack
      sx={{
        gap: 0.5,
      }}
    >
      <Stack
        direction="row"
        sx={{
          justifyContent: "space-between",
          alignItems: "center",
          gap: 2,
        }}
      >
        <FormLabel>{header}</FormLabel>
        {hasDateValues ? (
          <Button
            startIcon={<Close />}
            size="small"
            variant="outlined"
            onClick={() => {
              column.setFilterValue(undefined);
            }}
          >
            Clear date filter
          </Button>
        ) : null}
      </Stack>
      <Stack
        direction="row"
        sx={{
          gap: 1,
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <LocalizationProvider dateAdapter={AdapterDateFns}>
          <Stack>
            <DatePicker
              label="From"
              value={
                dateValues?.[0] ? new Date(dateValues[0] + "T00:00:00") : null
              }
              onChange={(date) => {
                if (!date) return;
                const dateStr = formatDateToYYYYMMDD(date);
                column.setFilterValue((old: [string, string]) => {
                  if (dateStr > old?.[1]) {
                    return old;
                  }
                  if (!isValidDateString(dateStr)) return old;

                  return [dateStr, old?.[1] || smallestMax];
                });
              }}
              minDate={min ? new Date(min + "T00:00:00") : undefined}
              maxDate={
                smallestMax ? new Date(smallestMax + "T00:00:00") : undefined
              }
              onError={(error) => {
                if (!dateValues?.[0]) return;
                setMinError(error);
              }}
            />
            <ErrorHelperText error={dateValues?.[0] ? minError : null} />
          </Stack>
          <Stack>
            <DatePicker
              label="To"
              value={
                dateValues?.[1] ? new Date(dateValues[1] + "T00:00:00") : null
              }
              onChange={(date) => {
                if (!date) return;
                const dateStr = formatDateToYYYYMMDD(date);
                column.setFilterValue((old: [string, string]) => {
                  if (dateStr < old?.[0]) {
                    return old;
                  }
                  if (!isValidDateString(dateStr)) return old;
                  return [old?.[0] || greatestMin, dateStr];
                });
              }}
              minDate={
                greatestMin ? new Date(greatestMin + "T00:00:00") : undefined
              }
              maxDate={max ? new Date(max + "T00:00:00") : undefined}
              onError={(error) => {
                if (!dateValues?.[1]) return;
                setMaxError(error);
              }}
            />
            <ErrorHelperText error={dateValues?.[1] ? maxError : null} />
          </Stack>
        </LocalizationProvider>
      </Stack>
    </Stack>
  );
};

const ErrorHelperText = ({ error }: { error: DateValidationError }) => {
  const text = error
    ? {
        invalidDate: "Invalid date",
        invalidRange: "Invalid range",
        disableFuture: "Disable future",
        disablePast: "Disable past",
        maxDate: "Date is greater than maximum date",
        minDate: "Date is less than minimum date",
        shouldDisableDate: "Should disable date",
        shouldDisableMonth: "Should disable month",
        shouldDisableYear: "Should disable year",
      }[error]
    : " ";
  return <FormHelperText error>{text}</FormHelperText>;
};
