import Button from "@mui/material/Button";
import Dialog, { DialogProps } from "@mui/material/Dialog";
import DialogActions from "@mui/material/DialogActions";
import DialogContent from "@mui/material/DialogContent";
import DialogTitle from "@mui/material/DialogTitle";
import TextField from "@mui/material/TextField";
import * as React from "react";
import { ComponentProps, useState } from "react";

interface IDialogEditFieldProps {
  open: boolean;
  onClose: () => void;
  onSubmit: (value: string) => void;
  initialValue: string;
  /**
   * The text to display in the dialog such as "Enter a new name"
   */
  message: string;
  dialogProps?: Omit<DialogProps, "open" | "onClose">;
  textFieldProps?: Omit<ComponentProps<typeof TextField>, "onChange">;
}

export const DialogEditField = (props: IDialogEditFieldProps) => {
  const { open, onClose, message, onSubmit, initialValue } = props;
  const [value, setValue] = useState<string>(initialValue);

  const handleSubmit = () => {
    onSubmit(value);
  };

  return (
    <Dialog open={open} onClose={onClose} {...props.dialogProps}>
      <DialogTitle>{message}</DialogTitle>
      <DialogContent>
        <TextField
          autoFocus
          required
          margin="dense"
          variant={"standard"}
          fullWidth
          {...props.textFieldProps}
          onChange={(e) => setValue(e.target.value)}
          value={value}
          helperText={!value.trim() && "This field is required"}
          error={!value.trim()}
        />
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button onClick={handleSubmit} disabled={!value.trim()}>
          Submit
        </Button>
      </DialogActions>
    </Dialog>
  );
};
