import MenuItem from "@mui/material/MenuItem";
import TextField, { TextFieldProps } from "@mui/material/TextField";
import {
  Control,
  FieldPath,
  FieldValues,
  PathValue,
  useController,
} from "react-hook-form";

type TOptionMap = {
  id: string | number;
  value: string;
}[];

interface SelectElementProps<
  Values extends FieldValues,
  Options extends TOptionMap,
> {
  control: Control<Values>;
  name: FieldPath<Values>;
  label: string;
  defaultValue: PathValue<Values, FieldPath<Values>>;
  options: Options;
  textFieldProps?: TextFieldProps;
}

/**
 * SelectElement
 * @description A select element that integrates with react-hook-form and MUI select
 *
 */
export const SelectElement = <
  Values extends FieldValues,
  Options extends TOptionMap,
>(
  props: SelectElementProps<Values, Options>,
): JSX.Element => {
  const { control, name, label, defaultValue, options, textFieldProps } = props;
  const { field, fieldState } = useController<Values>({
    name,
    control,
    defaultValue,
  });

  return (
    <TextField
      select
      fullWidth
      variant="filled"
      size="small"
      label={label}
      onChange={field.onChange}
      onBlur={field.onBlur}
      value={field.value}
      name={field.name}
      inputRef={field.ref}
      error={!!fieldState.error}
      {...textFieldProps}
    >
      {options.map((option) => (
        <MenuItem key={option.id} value={option.id}>
          {option.value}
        </MenuItem>
      ))}
    </TextField>
  );
};
