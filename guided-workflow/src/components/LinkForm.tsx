import AddIcon from "@mui/icons-material/Add";
import CloseIcon from "@mui/icons-material/Close";
import Button from "@mui/material/Button";
import Dialog from "@mui/material/Dialog";
import DialogActions from "@mui/material/DialogActions";
import DialogContent from "@mui/material/DialogContent";
import DialogTitle from "@mui/material/DialogTitle";
import FormControl from "@mui/material/FormControl";
import FormHelperText from "@mui/material/FormHelperText";
import IconButton from "@mui/material/IconButton";
import InputLabel from "@mui/material/InputLabel";
import MenuItem from "@mui/material/MenuItem";
import Select from "@mui/material/Select";
import TextField from "@mui/material/TextField";
import { useState } from "react";
import { Controller, useForm } from "react-hook-form";

import { LinkSchema } from "~/domain/Engagement";
import { useLink } from "~/features/links/useLink";
import { returnParsedData } from "~/utils/safeParse";

const LinkTypes = {
  acat_links: "ACAT Link",
  mce_links: "MCE Link",
  party_links: "Party Link",
  smart_links: "Smart Link",
};

export const emptyLink = {
  id: 0,
  linkType: "acat_links",
};

const LinkForm = ({ engagementId }: { engagementId: number }) => {
  const {
    control,
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm({
    defaultValues: {
      id: "",
      link_type: "",
      dc_engagement_id: engagementId,
    },
  });

  const [open, setOpen] = useState(false);

  const onClose = () => {
    setOpen(false);
  };

  const onOpen = () => {
    setOpen(true);
  };

  const { onCreate } = useLink(engagementId);

  const onSubmit = (data: {
    id: string;
    dc_engagement_id: number;
    link_type: string;
  }) => {
    const parsedFormData = returnParsedData(data, LinkSchema);
    if (!parsedFormData) return;
    onCreate(parsedFormData);
    reset();
    onClose();
  };

  return (
    <>
      <Button variant="contained" onClick={onOpen} startIcon={<AddIcon />}>
        Add Link
      </Button>
      <Dialog fullWidth maxWidth="sm" open={open} onClose={onClose}>
        <DialogTitle>Add Link</DialogTitle>
        <IconButton
          edge="end"
          color="inherit"
          onClick={onClose}
          aria-label="close"
          style={{ position: "absolute", right: "20px", top: "8px" }}
        >
          <CloseIcon />
        </IconButton>
        <form onSubmit={handleSubmit(onSubmit)}>
          <DialogContent
            sx={{
              display: "flex",
              flexDirection: "column",
              gap: "1rem",
            }}
          >
            <TextField
              id="id"
              label="ID"
              type="number"
              {...register("id", { required: true })}
              fullWidth
            />
            <FormControl fullWidth error={!!errors.link_type} required>
              <InputLabel id="link_type-label">Link Type</InputLabel>
              <Controller
                name="link_type"
                control={control}
                rules={{ required: "Link Type is required" }}
                render={({ field }) => (
                  <Select labelId="link_type-label" {...field}>
                    {Object.entries(LinkTypes).map(([value, label]) => (
                      <MenuItem key={value} value={value}>
                        {label}
                      </MenuItem>
                    ))}
                  </Select>
                )}
              />
              {errors.link_type && (
                <FormHelperText>{errors.link_type.message}</FormHelperText>
              )}
            </FormControl>
          </DialogContent>
          <DialogActions>
            <Button
              sx={{
                backgroundColor: "#1976d2",
                color: "white",
                fontSize: "1rem",
                "&:hover": {
                  color: "#1976d2",
                  backgroundColor: "white",
                },
              }}
              type="submit"
              variant="contained"
            >
              Submit
            </Button>
          </DialogActions>
        </form>
      </Dialog>
    </>
  );
};

export default LinkForm;
