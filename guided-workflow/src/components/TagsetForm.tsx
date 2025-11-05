import AddIcon from "@mui/icons-material/Add";
import ArchiveIcon from "@mui/icons-material/Archive";
import CloseIcon from "@mui/icons-material/Close";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Dialog from "@mui/material/Dialog";
import DialogActions from "@mui/material/DialogActions";
import DialogContent from "@mui/material/DialogContent";
import DialogTitle from "@mui/material/DialogTitle";
import IconButton from "@mui/material/IconButton";
import TextField from "@mui/material/TextField";
import { useMutation } from "@tanstack/react-query";
import { saveAs } from "file-saver";
import { useState } from "react";
import { Controller, useFieldArray, UseFormReturn } from "react-hook-form";
import { toast } from "sonner";

import { extractTagsets } from "~/api/tagset";
import { TTagset } from "~/domain/Tagset";

import { useCreateTagset } from "./useCreateTagset";

const TagSetForm = ({
  engagementId,
  formMethods,
}: {
  engagementId?: number;
  formMethods: UseFormReturn<TTagset>;
}) => {
  const formattedDate = `${new Date().getFullYear()} ${(
    "0" +
    (new Date().getMonth() + 1)
  ).slice(-2)} ${("0" + new Date().getDate()).slice(-2)}`;
  const {
    register,
    control,
    handleSubmit,
    formState: { errors },
  } = formMethods;
  const { fields, append, remove } = useFieldArray({
    control,
    name: "tags",
  });

  const [open, setOpen] = useState(false);

  const onClose = () => {
    setOpen(false);
  };

  const onOpen = () => {
    setOpen(true);
  };

  const onCreateTagset = useCreateTagset(engagementId);

  const onSubmit = async (data: TTagset) => {
    onCreateTagset(data, () => onClose());
  };

  const { mutateAsync } = useMutation({
    mutationFn: async () => {
      if (!engagementId) return;
      const blob = await extractTagsets(engagementId);
      saveAs(
        blob,
        `File_Upload_Template_TagSet_${engagementId}_${formattedDate}`,
      );
    },
  });

  const handleExtractTagsets = () => {
    toast.promise(mutateAsync(), {
      loading: "Extracting tagsets...",
      success: "Tagsets extracted successfully",
      error: "Error extracting tagsets",
    });
  };

  return (
    <>
      <Box
        sx={{
          display: "flex",
          gap: 1,
        }}
      >
        {engagementId ? (
          <Button
            onClick={handleExtractTagsets}
            variant="contained"
            startIcon={<ArchiveIcon />}
          >
            Extract Tagsets
          </Button>
        ) : null}
        <Button onClick={onOpen} variant="contained" startIcon={<AddIcon />}>
          Add Tagset
        </Button>
      </Box>
      <Dialog maxWidth="sm" fullWidth open={open} onClose={onClose}>
        <DialogTitle>Add TagSet</DialogTitle>
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
            <Controller
              name="tagset_name"
              control={control}
              rules={{
                required: true,
                validate: {
                  noNumberFirst: (value) => {
                    // Check if the first character is a number
                    if (/^\d/.test(value)) {
                      return "The first character can't be a number";
                    }
                    return true;
                  },
                  maxLength: (value) => {
                    if (value.length > 250) {
                      return "Keep it under 250 characters!";
                    }
                    return true;
                  },
                },
              }}
              render={({ field }) => (
                <TextField
                  {...field}
                  label="TagSet Name"
                  fullWidth
                  error={Boolean(errors.tagset_name)}
                  helperText={errors.tagset_name?.message} // Add this to display the error message
                  slotProps={{
                    htmlInput: { maxLength: 250 },
                  }}
                />
              )}
            />

            <TextField
              label="TagSet Description"
              {...register("tagset_desc")}
              fullWidth
            />
            <TextField
              label="Scope"
              {...register("scope")}
              placeholder="Engagement"
              defaultValue={engagementId ? "Engagement" : "Global"}
              hidden={!engagementId}
            />
            {engagementId && (
              <>
                <TextField
                  label="Engagement"
                  {...register("dc_engagement_id")}
                  placeholder="Engagement"
                  defaultValue={engagementId}
                  hidden
                />
                <TextField
                  label="TagSet Type"
                  type="number"
                  {...register("tagset_type")}
                  placeholder={"1"}
                  defaultValue={"1"}
                  hidden
                />
              </>
            )}

            <TextField
              label="Cardinality"
              {...register("cardinality")}
              placeholder="1:1"
              defaultValue="1:1"
              hidden
            />
            <Box
              sx={{
                display: "flex",
                flexDirection: "column",
              }}
            >
              {fields.map((field, index) => (
                <Box key={field.id}>
                  <TextField
                    label="Tag Name"
                    {...register(`tags.${index}.tag_name`, { required: true })}
                  />
                  {errors.tags && errors.tags[index]?.tag_name && (
                    <p>please enter Tag Name</p>
                  )}
                  <TextField
                    label="Tag Description"
                    {...register(`tags.${index}.tag_desc`)}
                  />
                  <Button onClick={() => remove(index)}>Remove</Button>
                </Box>
              ))}
              <Button
                variant="contained"
                sx={{
                  backgroundColor: "#1976d2",
                  color: "white",
                  fontSize: "1rem",
                  "&:hover": {
                    color: "#1976d2",
                    backgroundColor: "white",
                  },
                }}
                onClick={() =>
                  append({
                    tag_name: "",
                    tag_desc: "",
                    tagset_id: new Date().getTime(),
                    tag_id: 0,
                  })
                }
              >
                Add Tag
              </Button>
            </Box>
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

export default TagSetForm;
