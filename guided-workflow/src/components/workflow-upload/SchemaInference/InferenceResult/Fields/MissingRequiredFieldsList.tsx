import WarningIcon from "@mui/icons-material/Warning";
import { Box, Stack, Typography } from "@mui/material";
import { LayoutGroup } from "framer-motion";

import { AnimateIn } from "~/components/workflow-upload/SchemaInference/InferenceResult/AnimatedComponents";

export interface IMissingRequiredFieldsListProps {
  missingRequired: string[];
}

export const MissingRequiredFieldsList = ({
  missingRequired,
}: IMissingRequiredFieldsListProps) => (
  <Box mb={2}>
    <Stack direction="row" alignItems="center" spacing={1}>
      <LayoutGroup>
        <AnimateIn sequenceNumber={3} layoutId={"missing-required-header"}>
          <Typography variant="h6">Missing Required Fields</Typography>
        </AnimateIn>
      </LayoutGroup>
      <WarningIcon sx={{ color: "error.main" }} />
    </Stack>
    <AnimateIn sequenceNumber={4} layoutId={"missing-required-fields"}>
      <Stack direction="row" flexWrap="wrap" gap={1}>
        <LayoutGroup>
          {missingRequired.map((field) => (
            <Box
              key={field}
              sx={{
                border: "1px solid #ccc",
                borderRadius: 1,
                p: 1,
                m: 0.5,
                flexGrow: 1,
                minWidth: 150,
                flexBasis: "min-content",
              }}
            >
              <Typography variant="subtitle1">{field}</Typography>
            </Box>
          ))}
        </LayoutGroup>
      </Stack>
    </AnimateIn>
  </Box>
);
