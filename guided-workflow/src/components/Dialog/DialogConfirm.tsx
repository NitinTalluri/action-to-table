import Button from "@mui/material/Button";
import Dialog, { DialogProps } from "@mui/material/Dialog";
import DialogActions from "@mui/material/DialogActions";
import DialogContent from "@mui/material/DialogContent";
import DialogContentText from "@mui/material/DialogContentText";

export type TDialogConfirmProps = {
  open: boolean;
  message: string;
  onAction: (e: "confirm" | "cancel") => void;
  dialogProps?: Omit<DialogProps, "open" | "onClose">;
  variant?: "default" | "error";
};
const DialogConfirm = (props: TDialogConfirmProps) => {
  const { message, onAction, open, dialogProps, variant } = props;

  const handleClose = () => {
    onAction("cancel");
  };

  const handleConfirm = () => {
    onAction("confirm");
  };

  return (
    <Dialog open={open} onClose={handleClose} {...dialogProps}>
      <DialogContent>
        <DialogContentText>{message}</DialogContentText>
      </DialogContent>
      <DialogActions>
        <Button onClick={handleClose}>Cancel</Button>
        <Button
          color={variant === "error" ? "error" : "primary"}
          variant="contained"
          onClick={handleConfirm}
        >
          Confirm
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default DialogConfirm;
