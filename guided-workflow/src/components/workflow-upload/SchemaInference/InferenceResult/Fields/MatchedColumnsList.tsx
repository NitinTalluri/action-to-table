import { Box, Stack } from "@mui/material";
import Typography from "@mui/material/Typography";

import {
  AnimatedHeader,
  AnimatedMembers,
  MemberContainer,
} from "~/components/workflow-upload/SchemaInference/InferenceResult";

export type TMatchedColumnsList = {
  members: {
    displayName: string;
    fieldName: string;
  }[];
};

const ResolvedMember = ({
  displayName,
  fieldName,
}: {
  displayName: string;
  fieldName: string;
}) => {
  return (
    <MemberContainer>
      <Typography variant="subtitle1" sx={{ fontSize: ".9rem", lineHeight: 1 }}>
        {displayName}
      </Typography>
      <Typography
        variant="caption"
        sx={{
          color: "text.secondary",
          fontSize: ".75rem",
          pt: 0,
          mt: 0,
          lineHeight: 1,
        }}
      >
        Resolved as: {fieldName}
      </Typography>
    </MemberContainer>
  );
};

export const MatchedColumnsList = ({ members }: TMatchedColumnsList) => (
  <Box mb={2}>
    <AnimatedHeader>
      <Typography variant="h6">Resolved Columns</Typography>
    </AnimatedHeader>
    <AnimatedMembers>
      <Stack direction={"row"} flexWrap={"wrap"}>
        {members.map((c) => (
          <ResolvedMember
            key={`${c.displayName}-${c.fieldName}`}
            displayName={c.displayName}
            fieldName={c.fieldName}
          />
        ))}
      </Stack>
    </AnimatedMembers>
  </Box>
);
