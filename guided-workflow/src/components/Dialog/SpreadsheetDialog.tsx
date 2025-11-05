import DataGridXL from "@datagridxl/datagridxl2";
import CloseIcon from "@mui/icons-material/Close";
import { DialogContentText } from "@mui/material";
import Dialog from "@mui/material/Dialog";
import DialogContent from "@mui/material/DialogContent";
import DialogTitle from "@mui/material/DialogTitle";
import IconButton from "@mui/material/IconButton";
import Typography from "@mui/material/Typography";
import React, { useEffect, useState } from "react";

import useGridRef from "../../hooks/useGridRef";

export type TColumnOptions = {
  title: string;
  source: number;
  width?: number;
};

export interface ISpreadsheetDialog {
  open: boolean;
  onClose: () => void;
  title: string;
  data: string[][] | null;
  columns: TColumnOptions[] | null;
}

const readOnlyConfig = {
  allowInsertRows: false,
  allowDeleteRows: false,
  allowMoveRows: false,
  allowInsertCols: false,
  allowDeleteCols: false,
  allowMoveCols: false,
  allowFillCells: false,
  allowEditCells: false,
  // disallow clipboard
  allowCut: false,
  allowPaste: false,
  // still allow copy & col resize (default)
  allowResizeCols: true,
  allowCopy: true,
};
const SpreadsheetDialog = (props: ISpreadsheetDialog) => {
  /**
   * Read only spreadsheet dialog
   */

  // Ref will come from MUI Dialog
  const { data, columns, open, onClose, title } = props;
  const gridRef = useGridRef();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    const tryRemoveGrid = () => {
      if (gridRef.current && gridRef.current.grid) {
        gridRef.current.grid.destroy();
      }
    };
    if (!open) {
      return tryRemoveGrid();
    }

    const initOptions = {
      data: data || undefined,
      columns: columns || undefined,
      colWidth: 100,
      ...readOnlyConfig,
    };

    if (gridRef.current && !gridRef.current.grid) {
      gridRef.current.grid = new DataGridXL(gridRef.current, initOptions);
    }
  }, [columns, data, gridRef, mounted, open]);

  const handleDialogMounted = () => {
    setMounted(true);
  };

  const handleDialogUnmounted = () => {
    setMounted(false);
  };

  return (
    <Dialog
      maxWidth={"xl"}
      fullWidth
      open={open}
      onClose={onClose}
      TransitionProps={{
        onEntered: handleDialogMounted,
        onExited: handleDialogUnmounted,
      }}
    >
      <DialogTitle>
        <Typography variant={"body1"}>{title}</Typography>
        <IconButton
          edge="end"
          color="inherit"
          onClick={onClose}
          aria-label="close"
          sx={{ position: "absolute", right: 24, top: 8 }}
        >
          <CloseIcon />
        </IconButton>
      </DialogTitle>
      <DialogContent
        sx={{
          height: "40vh",
          width: "100%",
          padding: "10px",
          display: "flex",
          justifyContent: "center",
        }}
      >
        <DialogContentText
          sx={{
            height: "100%",
            display: "block",
            width: "90%",
            boxSizing: "content-box",
          }}
          ref={gridRef}
        />
      </DialogContent>
    </Dialog>
  );
};

export default SpreadsheetDialog;
