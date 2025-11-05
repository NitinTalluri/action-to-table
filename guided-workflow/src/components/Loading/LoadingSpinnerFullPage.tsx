import Box from "@mui/material/Box";
import CircularProgress from "@mui/material/CircularProgress";

const LoadingSpinnerFullPage = () => {
  return (
    <Box sx={{ maxWidth: "100vw" }}>
      <Box
        sx={{
          display: "flex",
          justifyContent: "center",
          height: "100vh",
          alignItems: "center",
        }}
      >
        <CircularProgress disableShrink />
      </Box>
    </Box>
  );
};

export default LoadingSpinnerFullPage;
