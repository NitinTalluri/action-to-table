import { TextField } from "@mui/material";
import Autocomplete from "@mui/material/Autocomplete";
import {
  Control,
  FieldPath,
  FieldValues,
  PathValue,
  useController,
} from "react-hook-form";

import { useSelectionHistory } from "./history";

interface SelectElementWithHistoryProps<Values extends FieldValues> {
  control: Control<Values>;
  name: FieldPath<Values>;
  label: string;
  defaultValue: PathValue<Values, FieldPath<Values>>;
  historyKey: string;
  maxHistory?: number;
}

export const SelectElementWithHistory = <Values extends FieldValues>(
  props: SelectElementWithHistoryProps<Values>,
) => {
  const { control, name, label, defaultValue, historyKey, maxHistory } = props;
  const [selectionHistory] = useSelectionHistory({
    key: historyKey,
    maxHistory,
  });
  const { field, fieldState } = useController<Values>({
    name,
    control,
    defaultValue,
  });

  return (
    <Autocomplete
      id={historyKey}
      freeSolo
      value={field.value}
      onChange={(_, newValue) => field.onChange(newValue)}
      renderInput={(params) => (
        <TextField
          {...params}
          fullWidth
          label={label}
          onChange={field.onChange}
          onBlur={field.onBlur}
          value={field.value}
          name={field.name}
          inputRef={field.ref}
          error={!!fieldState.error}
          helperText={fieldState.error?.message}
        />
      )}
      options={selectionHistory.map((opt) => opt.value)}
    />
  );
};
