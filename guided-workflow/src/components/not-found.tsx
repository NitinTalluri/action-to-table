import WrongLocationIcon from "@mui/icons-material/WrongLocation";
import { Stack, Typography } from "@mui/material";

export const NotFound = () => {
  return (
    <Stack
      spacing={1}
      sx={{ height: "100%" }}
      alignItems={"center"}
      justifyContent={"center"}
    >
      <WrongLocationIcon sx={{ fontSize: 100 }} />
      <Typography variant="h1">404</Typography>
      <Typography>Oops, we couldn't find what you're looking for</Typography>
    </Stack>
  );
};
