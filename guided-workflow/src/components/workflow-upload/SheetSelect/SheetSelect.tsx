import { Box } from "@mui/material";
import Button from "@mui/material/Button";
import Dialog from "@mui/material/Dialog";
import DialogContent from "@mui/material/DialogContent";
import DialogTitle from "@mui/material/DialogTitle";
import { FC } from "react";

import { DialogCloseButton } from "~/components/Dialog";

const SheetSelectButtons: FC<{
  sheetNames: string[];
  handleSheetSelect: (name: string) => void;
}> = ({ sheetNames, handleSheetSelect }) => (
  <Box sx={{ display: "flex", flexDirection: "column", gap: 1 }}>
    {sheetNames.map((name) => (
      <Button
        key={name}
        onClick={() => handleSheetSelect(name)}
        variant="outlined"
      >
        {name}
      </Button>
    ))}
  </Box>
);
export const SheetSelectDialog: FC<{
  open: boolean;
  fileName: string;
  sheetNames: string[];
  handleSheetSelect: (name: string) => void;
  handleClose: () => void;
}> = ({ open, handleSheetSelect, handleClose, sheetNames }) => {
  return (
    <Dialog
      open={open}
      disableEscapeKeyDown
      maxWidth="xs"
      fullWidth
      slotProps={{ paper: { sx: { p: 2 } }, transition: {} }}
    >
      <DialogTitle>
        Select a sheet
        <DialogCloseButton handleClose={handleClose} />
      </DialogTitle>
      <DialogContent>
        <SheetSelectButtons
          sheetNames={sheetNames}
          handleSheetSelect={handleSheetSelect}
        />
      </DialogContent>
    </Dialog>
  );
};
