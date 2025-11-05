import { Box, Stack } from "@mui/material";
import Typography from "@mui/material/Typography";

import {
  AnimatedHeader,
  AnimatedMembers,
  MemberContainer,
} from "~/components/workflow-upload/SchemaInference/InferenceResult";

export type TMissingDefaultableFieldsList = {
  members: string[];
};

const MissingDefaultableMember = ({ displayName }: { displayName: string }) => {
  return (
    <MemberContainer>
      <Typography variant="subtitle1" sx={{ fontSize: ".9rem", lineHeight: 1 }}>
        {displayName}
      </Typography>
    </MemberContainer>
  );
};

export const MissingDefaultableFieldsList = ({
  members,
}: TMissingDefaultableFieldsList) => (
  <Box mb={2}>
    <AnimatedHeader>
      <Typography variant="h6">Missing Optional Columns</Typography>
      <Typography variant="body2" color="text.secondary">
        These optional columns were not found
      </Typography>
    </AnimatedHeader>

    <AnimatedMembers>
      <Stack direction={"row"} flexWrap={"wrap"}>
        {members.map((displayName) => (
          <MissingDefaultableMember
            key={displayName}
            displayName={displayName}
          />
        ))}
      </Stack>
    </AnimatedMembers>
  </Box>
);
