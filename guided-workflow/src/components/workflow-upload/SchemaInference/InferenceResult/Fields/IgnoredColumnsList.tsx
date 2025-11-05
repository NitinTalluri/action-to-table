import { Box, Stack } from "@mui/material";
import Typography from "@mui/material/Typography";
import { LayoutGroup } from "framer-motion";

import {
  AnimatedHeader,
  AnimatedMembers,
} from "~/components/workflow-upload/SchemaInference/InferenceResult/AnimatedComponents";
import { MemberContainer } from "~/components/workflow-upload/SchemaInference/InferenceResult/Fields/MemberContainer";

export type TIgnoredColumnsList = {
  members: string[];
};

const IgnoredMember = ({ displayName }: { displayName: string }) => {
  return (
    <MemberContainer>
      <Typography variant="subtitle1" sx={{ fontSize: ".9rem", lineHeight: 1 }}>
        {displayName}
      </Typography>
    </MemberContainer>
  );
};

export const IgnoredColumnsList = ({ members }: TIgnoredColumnsList) => (
  <Box mb={2}>
    <AnimatedHeader>
      <Typography variant="h6">Ignored Columns</Typography>
      <Typography variant="body2" color="text.secondary">
        These columns will not be imported
      </Typography>
    </AnimatedHeader>
    <LayoutGroup>
      <AnimatedMembers>
        <Stack direction={"row"} flexWrap={"wrap"}>
          {members.map((displayName) => (
            <IgnoredMember key={displayName} displayName={displayName} />
          ))}
        </Stack>
      </AnimatedMembers>
    </LayoutGroup>
  </Box>
);
