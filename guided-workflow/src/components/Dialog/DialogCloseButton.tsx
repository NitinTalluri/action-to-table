import CloseIcon from "@mui/icons-material/Close";
import IconButton from "@mui/material/IconButton";
import React from "react";

type DialogCloseButtonProps = {
  handleClose: () => void;
};
export const DialogCloseButton = (props: DialogCloseButtonProps) => {
  return (
    <IconButton
      edge="end"
      color="inherit"
      onClick={() => props.handleClose()}
      aria-label="close"
      style={{
        position: "absolute",
        right: "1em",
        top: "0.5em",
      }}
    >
      <CloseIcon />
    </IconButton>
  );
};
