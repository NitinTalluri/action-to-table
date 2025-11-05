import { Chip } from "@mui/material";

export const SortIndicator = ({ index }: { index: number }) => (
  <Chip
    label={index + 1}
    size="small"
    color="primary"
    sx={{
      height: 20,
      fontSize: "0.75rem",
      fontWeight: "bold",
      marginLeft: 1,
      "& .MuiChip-label": {
        padding: "0 6px",
      },
    }}
  />
);
