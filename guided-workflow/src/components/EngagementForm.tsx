import AddIcon from "@mui/icons-material/Add";
import CloseIcon from "@mui/icons-material/Close";
import {
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  IconButton,
  TextField,
} from "@mui/material";
import { useState } from "react";
import { useForm } from "react-hook-form";

import { TEngagement } from "~/domain/Engagement";
import { useEngagement } from "~/features/engagements/useEngagement";

const EngagementForm = () => {
  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm<TEngagement>();
  const [open, setOpen] = useState(false);

  const onClose = () => {
    setOpen(false);
  };

  const onOpen = () => {
    setOpen(true);
  };

  const { onCreate } = useEngagement();

  const onSubmit = (data: TEngagement) => {
    onCreate(data);
    reset();
    onClose();
  };

  return (
    <>
      <Button startIcon={<AddIcon />} variant="contained" onClick={onOpen}>
        Add Engagement
      </Button>
      <Dialog maxWidth="sm" fullWidth open={open} onClose={onClose}>
        <DialogTitle>Engagement Create</DialogTitle>
        <IconButton
          edge="end"
          color="inherit"
          onClick={onClose}
          aria-label="close"
          style={{ position: "absolute", right: "20px", top: "8px" }}
        >
          <CloseIcon />
        </IconButton>
        <form onSubmit={handleSubmit(onSubmit)} noValidate>
          <DialogContent
            sx={{
              display: "flex",
              flexDirection: "column",
              gap: "1rem",
            }}
          >
            <TextField
              sx={{ marginTop: "1rem" }}
              label="Engagement Name"
              {...register("engagement_name", {
                required: "Engagement Name is required",
              })}
              error={Boolean(errors.engagement_name)}
              fullWidth
            />
            <TextField
              label="Notes"
              defaultValue=""
              {...register("notes")}
              fullWidth
            />
            <Box
              sx={{
                display: "flex",
                flexDirection: "row",
                justifyContent: "space-evenly",
              }}
            ></Box>
          </DialogContent>
          <DialogActions>
            <Button type="submit" variant="contained">
              Submit
            </Button>
          </DialogActions>
        </form>
      </Dialog>
    </>
  );
};

export default EngagementForm;
