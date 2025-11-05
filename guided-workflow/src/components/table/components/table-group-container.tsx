import { Card, Divider, Stack } from "@mui/material";
import { ReactNode } from "react";

export const TableGroupContainer = ({
  children,
  header,
}: {
  children: ReactNode;
  header: ReactNode;
}) => {
  return (
    <Card>
      <Stack>
        <Stack
          direction="row"
          sx={{
            padding: 1,
            gap: 1,
            alignItems: "center",
            justifyContent: "space-between",
          }}
        >
          {header}
        </Stack>
        <Divider />
        {children}
      </Stack>
    </Card>
  );
};
