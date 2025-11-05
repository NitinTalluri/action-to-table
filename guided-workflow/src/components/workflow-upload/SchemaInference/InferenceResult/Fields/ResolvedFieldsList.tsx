import { Box, Stack, Typography } from "@mui/material";
import { motion } from "framer-motion";

export interface IResolvedFieldsListProps {
  mapping: Record<string, string>;
}

export const ResolvedFieldsList = ({ mapping }: IResolvedFieldsListProps) => (
  <Box mb={2}>
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
    >
      <Typography variant="h6">Resolved Fields</Typography>
    </motion.div>
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: 0.4 }}
    >
      <Stack direction="row" flexWrap="wrap">
        {Object.entries(mapping).map(([excelHeader, schemaField]) => (
          <Box
            key={excelHeader}
            sx={{
              border: "1px solid #ccc",
              borderRadius: 1,
              p: 1,
              m: 0.5,
              flexGrow: 1,
              minWidth: 150,
            }}
          >
            <Typography variant="subtitle1">{excelHeader}</Typography>
            <Typography variant="caption" sx={{ color: "text.secondary" }}>
              Resolved as: {schemaField}
            </Typography>
          </Box>
        ))}
      </Stack>
    </motion.div>
  </Box>
);
