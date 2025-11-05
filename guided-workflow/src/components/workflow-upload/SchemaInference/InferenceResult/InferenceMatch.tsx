import ErrorOutlineIcon from "@mui/icons-material/ErrorOutline";
import { Alert, Box, Divider, Typography } from "@mui/material";

import {
  IgnoredColumnsList,
  MatchedColumnsList,
  MissingDefaultableFieldsList,
} from "~/components/workflow-upload/SchemaInference/InferenceResult/Fields";
import { ISchemaInferenceResult } from "~/domain/resolvers/schemaInferenceRegistry";

type TPerfectMatchProps = {
  result: ISchemaInferenceResult;
};

type TNoMatchProps = {
  result: ISchemaInferenceResult;
};

const Match = ({ result }: TPerfectMatchProps) => {
  const { mapping, ignoredColumns, missingOptionalFields } = result;
  const matchedColumns = Object.entries(mapping).map(
    ([displayName, fieldName]) => ({ displayName, fieldName }),
  );
  return (
    <Box>
      <MatchedColumnsList members={matchedColumns} />
      {missingOptionalFields.length > 0 && (
        <>
          <Divider sx={{ mb: 1 }} />
          <MissingDefaultableFieldsList members={missingOptionalFields} />
        </>
      )}
      {ignoredColumns.length > 0 && (
        <>
          <Divider sx={{ mb: 1 }} />
          <IgnoredColumnsList members={ignoredColumns} />
        </>
      )}
    </Box>
  );
};

const NoMatch = ({ result }: TNoMatchProps) => {
  const hasMissingRequired = result.missingRequired.length > 0;

  return (
    <Box>
      <Alert severity="error" sx={{ mb: 3 }}>
        <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 1 }}>
          <ErrorOutlineIcon />
          <Typography variant="h6">No Compatible Schema Found</Typography>
        </Box>
        <Typography variant="body2">
          {result.errorMessage ||
            "Unable to find a schema that matches your upload."}
        </Typography>
      </Alert>

      {hasMissingRequired && (
        <MissingDefaultableFieldsList members={result.missingRequired} />
      )}

      <Box sx={{ mb: 3 }}>
        <Typography variant="subtitle1" gutterBottom>
          What to try next:
        </Typography>
        <Box component="ul" sx={{ pl: 2, m: 0 }}>
          <Typography component="li" variant="body2" sx={{ mb: 0.5 }}>
            Check that your Excel file contains the required column headers
          </Typography>
          <Typography component="li" variant="body2" sx={{ mb: 0.5 }}>
            Verify column names match expected format (case-sensitive)
          </Typography>
          <Typography component="li" variant="body2" sx={{ mb: 0.5 }}>
            Ensure you've selected the correct sheet
          </Typography>
          <Typography component="li" variant="body2">
            Contact support if you believe this is an error
          </Typography>
        </Box>
      </Box>
    </Box>
  );
};

export const InferenceMatch = ({
  result,
}: TPerfectMatchProps | TNoMatchProps) => {
  if (result.isCompatible) {
    return <Match result={result} />;
  } else {
    return <NoMatch result={result} />;
  }
};
