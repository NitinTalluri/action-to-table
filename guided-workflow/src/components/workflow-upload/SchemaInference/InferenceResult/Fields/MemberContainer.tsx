import Box from "@mui/material/Box";
import { ReactNode } from "react";

/**
 * Designed for inline use with row wrap flex containers
 * @param children
 * @param key
 * @constructor
 */

export const MemberContainer = ({
  children,
  key,
}: {
  children: ReactNode;
  key?: string;
}) => {
  return (
    <Box
      key={key}
      sx={{
        border: "1px solid #ccc",
        borderRadius: 1,
        p: 1,
        m: 0.5,
        flexBasis: "fit-content",
        textWrap: "nowrap",
      }}
    >
      {children}
    </Box>
  );
};
