import Button from "@mui/material/Button";
import Dialog from "@mui/material/Dialog";
import DialogActions from "@mui/material/DialogActions";
import DialogContent from "@mui/material/DialogContent";
import DialogTitle from "@mui/material/DialogTitle";
import TextField, { TextFieldProps } from "@mui/material/TextField";
import { useState } from "react";

export interface ITextAreaDialog {
  open: boolean;
  onClose: () => void;
  onSubmit: (data: string) => void;
  title: string;
  textFieldProps?: TextFieldProps;
  isLoading?: boolean;
}

const TextAreaDialog = (props: ITextAreaDialog) => {
  const {
    open,
    onClose,
    onSubmit,
    title,
    textFieldProps,
    isLoading = false,
  } = props;
  const [text, setText] = useState<string>("");

  const handleSubmit = () => {
    onSubmit(text);
  };

  return (
    <div>
      <Dialog maxWidth="sm" fullWidth open={open}>
        <DialogTitle>{title}</DialogTitle>
        <DialogContent>
          <TextField
            placeholder="Add your comment..."
            multiline
            rows={4}
            onChange={(e) => setText(e.target.value)}
            {...textFieldProps}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={onClose}>Cancel</Button>
          <Button
            onClick={handleSubmit}
            variant="contained"
            loading={isLoading}
          >
            Submit
          </Button>
        </DialogActions>
      </Dialog>
    </div>
  );
};

export default TextAreaDialog;
