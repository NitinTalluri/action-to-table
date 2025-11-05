import { Typography } from "@mui/material";

import isDev from "~/utils/isDev";

export const AppTitle = () => {
  return (
    <div style={{ display: "flex" }}>
      <Typography fontSize="24px" fontWeight="bold">
        Data Canvas
      </Typography>
      {isDev && <sup style={{ fontSize: "0.7em", top: "0.5em" }}>dev</sup>}
    </div>
  );
};
