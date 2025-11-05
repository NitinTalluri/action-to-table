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
import { SubmitHandler, UseFormReturn } from "react-hook-form";

import { IStakeholderFormValues } from "~/domain/Stakeholder";
import { useStakeholder } from "~/features/stakeholder/useStakeholder";
import { useStakeHolderTableTypes } from "~/hooks/dcTypes";

type TStakeholderFormProps = {
  formMethods: UseFormReturn<IStakeholderFormValues>;
  engagement: number;
};

const StakeHolderForm = (props: TStakeholderFormProps) => {
  const { formMethods, engagement } = props;
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = formMethods;

  const { onCreate } = useStakeholder(engagement);

  const [open, setOpen] = useState(false);
  const { available: availableStakeholderTypes } = useStakeHolderTableTypes();

  const onClose = () => {
    setOpen(false);
    reset();
  };
  const onOpen = () => setOpen(true);

  const onSubmit: SubmitHandler<IStakeholderFormValues> = (
    data: IStakeholderFormValues,
  ) => {
    onCreate(data);
    onClose();
  };

  return (
    <div>
      <Button onClick={onOpen} variant="contained" startIcon={<AddIcon />}>
        Add Stakeholder
      </Button>
      <Dialog maxWidth="md" fullWidth open={open} onClose={onClose}>
        <DialogTitle>Add Stakeholder</DialogTitle>
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
              gap: "1.5rem",
            }}
          >
            <TextField
              id="-stakeholder_name"
              label="Name"
              type="text"
              {...register("stakeholder_name", {
                required: "Stakeholder Name Required",
              })}
              fullWidth
              error={Boolean(errors.stakeholder_name)}
              helperText={
                errors.stakeholder_name ? errors.stakeholder_name.message : null
              }
            />

            <TextField
              id="stakeholder_email"
              label="Email"
              type="text"
              {...register("stakeholder_email")}
              fullWidth
            />

            <TextField
              id="stakeholder_phone"
              label="Phone"
              type="text"
              {...register("stakeholder_phone")}
              fullWidth
            />

            <FormControl fullWidth>
              <InputLabel id="stakeholder_type_id-label">
                Stakeholder Type
              </InputLabel>
              <Select
                id={"stakeholder_type_id"}
                labelId="stakeholder_type_id-label"
                defaultValue={availableStakeholderTypes[0].id}
                {...register("stakeholder_type_id", {
                  required: "Stakeholder type is required",
                })}
                error={Boolean(errors.stakeholder_type_id)}
              >
                {availableStakeholderTypes.map((e) => (
                  <MenuItem key={e.id} value={e.id}>
                    {e.value}
                  </MenuItem>
                ))}
              </Select>
              {errors.stakeholder_type_id && (
                <FormHelperText>
                  {errors.stakeholder_type_id.message}
                </FormHelperText>
              )}
            </FormControl>
          </DialogContent>
          <DialogActions>
            <Button
              onClick={() => handleSubmit(onSubmit)}
              type="submit"
              variant="contained"
              color="primary"
              sx={{
                backgroundColor: "#1976d2",
                color: "white",
                fontSize: "1rem",
                "&:hover": {
                  color: "#1976d2",
                  backgroundColor: "white",
                },
              }}
            >
              Submit
            </Button>
          </DialogActions>
        </form>
      </Dialog>
    </div>
  );
};

export default StakeHolderForm;
