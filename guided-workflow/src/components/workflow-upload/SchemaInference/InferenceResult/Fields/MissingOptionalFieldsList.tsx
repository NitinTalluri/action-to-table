import InfoIcon from "@mui/icons-material/Info";
import { Box, Stack, Typography } from "@mui/material";
import { motion } from "framer-motion";

export interface IMissingOptionalFieldsListProps {
  missingDefaultableFields: string[];
}

export const MissingOptionalFieldsList = ({
  missingDefaultableFields,
}: IMissingOptionalFieldsListProps) => (
  <Box mb={2}>
    <Stack direction="row" alignItems="center" spacing={1}>
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, delay: 1.0 }}
      >
        <Typography variant="h6">Missing Optional Fields</Typography>
      </motion.div>
      <InfoIcon sx={{ color: "info.main" }} />
    </Stack>
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: 1.0 }}
    >
      <Typography variant="body2" sx={{ mb: 1, color: "text.secondary" }}>
        These optional fields will be auto-filled with null values
      </Typography>
      <Stack direction="row" flexWrap="wrap" gap={1}>
        {missingDefaultableFields.map((field) => (
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
      </Stack>
    </motion.div>
  </Box>
);
