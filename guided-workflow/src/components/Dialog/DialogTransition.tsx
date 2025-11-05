import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import CloseIcon from "@mui/icons-material/Close";
import { DialogActions, SxProps } from "@mui/material";
import Button from "@mui/material/Button";
import Dialog from "@mui/material/Dialog";
import DialogContent from "@mui/material/DialogContent";
import IconButton from "@mui/material/IconButton";
import LinearProgress from "@mui/material/LinearProgress";
import SvgIcon from "@mui/material/SvgIcon";
import Typography from "@mui/material/Typography";
import React, { useEffect, useState } from "react";

interface IDialogTransitionProps {
  open: boolean;
  onClose: (proceed: boolean) => void;
  durationMs?: number;
  title: string;
  Icon: typeof SvgIcon;
  iconSx?: SxProps;
}

const DialogTransition = (props: IDialogTransitionProps) => {
  const {
    onClose: handleClose,
    open,
    durationMs: durationMsParam,
    title,
    Icon,
    iconSx,
  } = props;
  const [progress, setProgress] = useState(0);
  const durationMs = durationMsParam ?? 7500;
  const drawIntervalMs = 100;

  useEffect(() => {
    if (!open) {
      return;
    }
    const increment = 100 / (durationMs / drawIntervalMs);
    const timer = setInterval(() => {
      setProgress((oldProgress) => {
        return Math.min(oldProgress + increment, 100);
      });
    }, drawIntervalMs);
    return () => {
      clearInterval(timer);
      setProgress(0);
    };
  }, [durationMs, open]);

  useEffect(() => {
    if (!open) {
      return;
    }
    const closeTimer = setTimeout(() => {
      handleClose(true);
    }, durationMs);
    return () => {
      clearTimeout(closeTimer);
    };
  }, [durationMs, handleClose, open]);

  const closeAndStay = () => handleClose(false);
  const closeAndProceed = () => handleClose(true);

  return (
    <Dialog open={open}>
      <div
        style={{
          display: "flex",
          justifyContent: "center",
          paddingTop: ".5rem",
        }}
      >
        <Typography sx={{ fontSize: "1.25rem" }}>{title}</Typography>
      </div>
      <IconButton
        edge="end"
        color="inherit"
        onClick={closeAndStay}
        aria-label="close"
        size={"small"}
        style={{
          position: "absolute",
          right: ".5rem",
          top: ".5rem",
          fontSize: ".5rem",
        }}
      >
        <CloseIcon />
      </IconButton>

      <DialogContent>
        <div style={{ display: "flex", justifyContent: "center" }}>
          <Icon sx={iconSx} />
        </div>
      </DialogContent>
      <DialogActions>
        <Button onClick={closeAndStay}>Stay Here</Button>
        <Button variant={"contained"} onClick={closeAndProceed}>
          Proceed
        </Button>
      </DialogActions>
      <div style={{ width: "100%" }}>
        <LinearProgress variant={"determinate"} value={progress} />
      </div>
    </Dialog>
  );
};

type TSuccessTransitionProps = Omit<IDialogTransitionProps, "Icon" | "iconSx">;

export const SuccessTransition = (props: TSuccessTransitionProps) => {
  return (
    <DialogTransition
      {...props}
      Icon={CheckCircleIcon}
      iconSx={{
        color: "green",
        height: "auto",
        width: "50%",
        padding: "0 2rem 0 2rem",
      }}
    />
  );
};
