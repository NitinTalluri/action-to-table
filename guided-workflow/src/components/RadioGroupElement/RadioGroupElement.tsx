import FormControl from "@mui/material/FormControl";
import FormControlLabel, {
  FormControlLabelProps,
} from "@mui/material/FormControlLabel";
import FormLabel from "@mui/material/FormLabel";
import Radio from "@mui/material/Radio";
import RadioGroup from "@mui/material/RadioGroup";
import { ChangeEvent } from "react";
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

interface RadioGroupElementProps<
  Values extends FieldValues,
  Options extends TOptionMap,
> {
  control: Control<Values>;
  name: FieldPath<Values>;
  label: string;
  labelProps?: Omit<FormControlLabelProps, "label" | "control" | "value">;
  defaultValue: PathValue<Values, FieldPath<Values>>;
  options: Options;
}

/**
 * RadioGroupElement
 * @description A Element that Renders Several Radio Buttons to work with react-hook-form and MUI RadioGroup
 *
 */
export const RadioGroupElement = <
  Values extends FieldValues,
  Options extends TOptionMap,
>(
  props: RadioGroupElementProps<Values, Options>,
) => {
  const { name, label, defaultValue, labelProps, options, control } = props;
  const { field } = useController<Values>({
    name,
    control,
    defaultValue,
  });

  const onRadioChange = (event: ChangeEvent<HTMLInputElement>) => {
    field.onChange(event.target.value);
  };

  return (
    <FormControl>
      <FormLabel>{label}</FormLabel>
      <RadioGroup {...field} onChange={onRadioChange}>
        {options.map((option) => {
          return (
            <FormControlLabel
              {...labelProps}
              control={<Radio checked={field.value === option.id} />}
              value={option.id}
              label={option.value}
              key={option.id}
            />
          );
        })}
      </RadioGroup>
    </FormControl>
  );
};
