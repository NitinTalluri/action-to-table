import {
  FormControl,
  FormControlLabel,
  Radio,
  RadioGroup,
  Stack,
  Typography,
} from "@mui/material";
import React from "react";

import { TagOption } from "~/domain/thoughtspot";

type TagOptionsRadioGroupProps = {
  value: TagOption;
  onChange: (value: TagOption) => void;
};

const TagOptionsRadioGroup: React.FC<TagOptionsRadioGroupProps> = ({
  value,
  onChange,
}) => {
  const handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    onChange(event.target.value as TagOption);
  };

  return (
    <FormControl component="fieldset">
      <RadioGroup
        aria-label="tag options"
        name="tag-options"
        value={value}
        onChange={handleChange}
      >
        <Typography
          variant="caption"
          sx={{
            color: "textSecondary",
          }}
        >
          Instance Tagging
        </Typography>
        <Stack direction="row">
          <FormControlLabel
            value=""
            control={<Radio />}
            label="Tag Selected Instance_IDs"
            defaultChecked={true}
          />
          <FormControlLabel
            value="null"
            control={<Radio />}
            label="Tag Instances Where Null"
            defaultChecked={true}
          />
        </Stack>
        <Typography
          variant="caption"
          sx={{
            color: "textSecondary",
          }}
        >
          Config Tagging
        </Typography>
        <Stack direction="row">
          <FormControlLabel
            value="config-all"
            control={<Radio />}
            label="Tag & Overwrite the Full Config"
          />
          <FormControlLabel
            value="config-null"
            control={<Radio />}
            label="Tag Nulls on the Full Config"
          />
        </Stack>
      </RadioGroup>
    </FormControl>
  );
};

export default TagOptionsRadioGroup;
