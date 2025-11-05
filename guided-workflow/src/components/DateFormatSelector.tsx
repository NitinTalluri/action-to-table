import {
  Checkbox,
  FormControl,
  FormControlLabel,
  FormGroup,
  FormLabel,
  Stack,
} from "@mui/material";

import {
  DateFormatEnum,
  ISOFormat,
  TDateFormatEnum,
} from "~/domain/grids/Cell";

type DateFormatSelectorProps = {
  dateFormat: TDateFormatEnum;
  setDateFormat: (newDateFormat: TDateFormatEnum) => void;
};

const DateFormatSelector = ({
  dateFormat,
  setDateFormat,
}: DateFormatSelectorProps) => {
  const dateFormats = DateFormatEnum.options;

  const handleDateFormatChange = (
    newValue: TDateFormatEnum,
    checked: boolean,
  ) => {
    if (dateFormat === newValue) {
      setDateFormat(checked ? newValue : ISOFormat.value);
    } else {
      setDateFormat(newValue);
    }
  };

  return (
    <Stack sx={{ mt: 2 }}>
      <FormControl>
        <FormLabel>Select Date Format</FormLabel>
        <FormGroup row>
          {dateFormats.map((f, i) => {
            return (
              <FormControlLabel
                key={`${f}-${i}`}
                control={
                  <Checkbox
                    checked={f === dateFormat}
                    name={f}
                    onChange={(e) =>
                      handleDateFormatChange(f, e.target.checked)
                    }
                  />
                }
                label={f.toUpperCase()}
              />
            );
          })}
        </FormGroup>
      </FormControl>
    </Stack>
  );
};

export default DateFormatSelector;
