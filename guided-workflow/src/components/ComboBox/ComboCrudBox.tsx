import DeleteIcon from "@mui/icons-material/Delete";
import EditIcon from "@mui/icons-material/Edit";
import Autocomplete, { createFilterOptions } from "@mui/material/Autocomplete";
import CircularProgress from "@mui/material/CircularProgress";
import IconButton from "@mui/material/IconButton";
import ListItemIcon from "@mui/material/ListItemIcon";
import ListItemText from "@mui/material/ListItemText";
import MenuItem from "@mui/material/MenuItem";
import TextField, { TextFieldProps } from "@mui/material/TextField";
import Tooltip from "@mui/material/Tooltip";
import {
  Control,
  FieldPath,
  FieldValues,
  useController,
} from "react-hook-form";

export type TOption = {
  id: string | number;
  value: string;
  inputValue?: string;
};

interface ComboCrudBoxProps<
  Values extends FieldValues,
  Options extends TOption,
> {
  control: Control<Values>;
  name: FieldPath<Values>;
  label: string;
  options: Options[];
  onCreateOption: (value: string) => void;
  onEditOption: (value: string, id: string | number) => void;
  onDeleteOption: (value: string, id: string | number) => void;
  isLoading: boolean;
  textFieldProps?: TextFieldProps;
}

/**
 * ComboCrudBox
 *
 * @description This integrates with MUI's Autocomplete component and react-hook-form
 * and allows users to create, edit and delete options
 */
export const ComboCrudBox = <
  Values extends FieldValues,
  Options extends TOption,
>(
  props: ComboCrudBoxProps<Values, Options>,
): JSX.Element => {
  const {
    control,
    name,
    label,
    textFieldProps,
    onCreateOption,
    onEditOption,
    onDeleteOption,
    isLoading,
    options,
  } = props;
  const filter = createFilterOptions<Options>();
  const { field, fieldState } = useController<Values>({
    name,
    control,
  });

  const currentValue =
    options.find((option) => option.id === field.value) ?? null;

  return (
    <Autocomplete
      freeSolo
      clearOnEscape
      multiple={false}
      id={name}
      value={currentValue}
      loading={isLoading}
      ref={field.ref}
      isOptionEqualToValue={(option, value) => {
        return option.id === value.id;
      }}
      getOptionLabel={(option) =>
        typeof option === "string" ? option : option.value
      }
      onChange={(_, value) => {
        // If it's a TOption, and has an inputValue then its a new option
        // If it's a TOption, and has an id then its an existing option
        if (typeof value === "string") {
          // Create a new option
          const matched = options.find((option) => option.value === value);
          if (matched) {
            return field.onChange(matched.id);
          }
          return onCreateOption(value);
        }
        if (value && value.inputValue) {
          // This was a suggestion - inputValue is what the user typed
          return onCreateOption(value.inputValue);
        }
        return field.onChange(value?.id ?? 0);
      }}
      options={options}
      filterOptions={(options, state) => {
        const filtered = filter(options, state);
        const { inputValue: inputRaw } = state;
        const inputValue = inputRaw.trim();
        // If this option is new, add an option for creating it
        const isExisting = options.some(
          (option) => inputValue === option.value,
        );

        if (inputValue !== "" && !isExisting) {
          filtered.push({
            value: `Add "${inputValue}"`,
            inputValue,
            id: -1,
          } as Options);
        }
        return filtered;
      }}
      renderOption={(props, option) => (
        <MenuItem {...props} key={props.key}>
          <ListItemText>{option.value}</ListItemText>
          <ListItemIcon>
            {option.id !== -1 && (
              <>
                <Tooltip title={"Edit"} placement={"left"}>
                  <IconButton
                    onClick={(e) => {
                      e.stopPropagation();
                      onEditOption(option.value, option.id);
                    }}
                  >
                    <EditIcon fontSize={"small"} />
                  </IconButton>
                </Tooltip>
                <Tooltip title={"Delete"} placement={"right"}>
                  <IconButton
                    onClick={(e) => {
                      e.stopPropagation();
                      onDeleteOption(option.value, option.id);
                    }}
                  >
                    <DeleteIcon fontSize={"small"} />
                  </IconButton>
                </Tooltip>
              </>
            )}
          </ListItemIcon>
        </MenuItem>
      )}
      renderInput={(params) => (
        <TextField
          {...params}
          fullWidth
          label={label}
          error={!!fieldState.error}
          helperText={fieldState.error?.message}
          {...textFieldProps}
          slotProps={{
            input: {
              ...params.InputProps,
              endAdornment: (
                <>
                  {isLoading ? (
                    <CircularProgress color="inherit" size={20} />
                  ) : null}
                  {currentValue && currentValue.id !== -1 && (
                    <Tooltip title={"Edit"}>
                      <IconButton
                        size={"small"}
                        onClick={(e) => {
                          e.stopPropagation();
                          onEditOption(currentValue.value, currentValue.id);
                        }}
                      >
                        <EditIcon fontSize={"small"} />
                      </IconButton>
                    </Tooltip>
                  )}
                  {currentValue && currentValue.id !== -1 && (
                    <Tooltip title={"Delete"}>
                      <IconButton
                        size={"small"}
                        onClick={() =>
                          onDeleteOption(currentValue.value, currentValue.id)
                        }
                      >
                        <DeleteIcon fontSize={"small"} />
                      </IconButton>
                    </Tooltip>
                  )}
                  {params.InputProps.endAdornment}
                </>
              ),
            },
          }}
        />
      )}
    />
  );
};
