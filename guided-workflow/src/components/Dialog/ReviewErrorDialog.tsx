import { Box } from "@mui/material";
import Button from "@mui/material/Button";
import Dialog, { DialogProps } from "@mui/material/Dialog";
import DialogActions from "@mui/material/DialogActions";
import DialogContent from "@mui/material/DialogContent";
import DialogTitle from "@mui/material/DialogTitle";
import { styled } from "@mui/material/styles";
import Table from "@mui/material/Table";
import TableBody from "@mui/material/TableBody";
import TableCell from "@mui/material/TableCell";
import TableHead from "@mui/material/TableHead";
import TableRow from "@mui/material/TableRow";
import Typography from "@mui/material/Typography";
import { useVirtualizer } from "@tanstack/react-virtual";
import { useRef } from "react";

import { DialogCloseButton } from "~/components/Dialog/DialogCloseButton";
import { TFlatError } from "~/hooks/useGridMethods";

interface ReviewErrorDialogProps {
  open: boolean;
  onClose: () => void;
  errors: TFlatError[] | null;
}

// We need to increase the z-index of the dialog so that it is above the grid
const StyledDialog = styled(Dialog)<DialogProps>(({ theme }) => ({
  ".MuiDialog-container": {
    zIndex: theme.zIndex.modal + 1,
  },
}));

const titleCaseColumn = (column: string) => {
  return column
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
};

const ErrorTable = <Schema,>(props: { errors: TFlatError[] }) => {
  const parentRef = useRef<HTMLDivElement>(null);
  const rowVirtualizer = useVirtualizer({
    count: props.errors.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 15,
    overscan: 5,
  });
  const items = rowVirtualizer.getVirtualItems();
  const { errors } = props;

  const columns = Object.keys(errors[0].row) as (keyof Schema & string)[];

  return (
    <Box
      ref={parentRef}
      sx={{
        overflowY: "auto",
        height: "100%",
      }}
    >
      <div
        style={{
          height: `${rowVirtualizer.getTotalSize()}px`,
          width: "100%",
          position: "relative",
        }}
      >
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Row Number</TableCell>
              {columns.map((column) => (
                <TableCell key={column}>{titleCaseColumn(column)}</TableCell>
              ))}
            </TableRow>
          </TableHead>
          <TableBody>
            {items.map((virtualItem, index) => {
              const matchedItem = errors[virtualItem.index];
              return (
                <TableRow
                  key={virtualItem.key}
                  ref={rowVirtualizer.measureElement}
                  data-index={virtualItem.index}
                  sx={{ borderCollapse: "unset" }}
                  style={{
                    transform: `translateY(${
                      virtualItem.start - index * virtualItem.size
                    }px)`,
                  }}
                >
                  <TableCell key={`${virtualItem.index}-'index'`}>
                    {matchedItem.rowIndex + 1}
                  </TableCell>
                  {columns.map((column) => (
                    <TableCell key={`${matchedItem.rowIndex}-${column}`}>
                      {matchedItem.row[column]}
                    </TableCell>
                  ))}
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </div>
    </Box>
  );
};
const ReviewErrorDialog = (props: ReviewErrorDialogProps) => {
  const { open, onClose, errors } = props;
  return (
    <StyledDialog open={open} onClose={onClose} maxWidth="xl" fullScreen>
      <DialogTitle>
        <Typography sx={{ fontSize: "1.5rem" }}>Review Errors</Typography>
        <DialogCloseButton handleClose={onClose} />
      </DialogTitle>
      <DialogContent>{errors && <ErrorTable errors={errors} />}</DialogContent>
      <DialogActions>
        <Button sx={{ padding: "10px 30px" }} size="large" onClick={onClose}>
          Back
        </Button>
      </DialogActions>
    </StyledDialog>
  );
};

export default ReviewErrorDialog;
