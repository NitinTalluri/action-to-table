import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import {
  AccordionSummary,
  Box,
  Button,
  Card,
  CardContent,
  Divider,
  LinearProgress,
  Typography,
} from "@mui/material";
import Accordion from "@mui/material/Accordion";
import AccordionDetails from "@mui/material/AccordionDetails";
import { useQuery } from "@tanstack/react-query";

import ComponentSkeleton from "~/components/Loading/ComponentSkeleton";
import { schemaInferenceQueryKeys } from "~/domain/resolvers/schemaInferenceQueryKeys";
import type {
  ISchemaInferenceResult,
  TSchemaInferenceNamespace,
} from "~/domain/resolvers/schemaInferenceRegistry";
import { useSheetReaderSchemaContext } from "~/hooks/upload/useExcelReader/SheetReaderContext";

import { InferenceMatch } from "./InferenceMatch";

type TSchemaInferenceResultContentProps = {
  isAnalyzing: boolean;
  result?: ISchemaInferenceResult<TSchemaInferenceNamespace>;
};

const SchemaInferenceResultContent = ({
  isAnalyzing,
  result,
}: TSchemaInferenceResultContentProps) => {
  if (isAnalyzing) {
    return <ComponentSkeleton />;
  }

  if (!result) {
    return null;
  }

  return <InferenceMatch result={result} />;
};

export type TPaginationProps = {
  paginate: (direction: "next" | "back") => void;
  activeStep: number;
  setActiveStep: (step: number) => void;
  onCancel: () => void;
};

type TSchemaInferenceResultComponentProps = {
  fileName: string | null;
  sheetName: string | null;
  namespace: TSchemaInferenceNamespace;
  paginationProps: TPaginationProps;
  onChangeSheet: () => void;
};

type TSchemaInferenceResultActiveProps = {
  fileName: string;
  sheetName: string;
  namespace: TSchemaInferenceNamespace;
  paginationProps: TPaginationProps;
  onChangeSheet: () => void;
};
const SchemaInferenceResultActive = ({
  fileName,
  sheetName,
  namespace,
  paginationProps,
  onChangeSheet,
}: TSchemaInferenceResultActiveProps) => {
  const sheetReader = useSheetReaderSchemaContext({ namespace });
  const queryPrefix = { namespace, fileName, sheetName };
  const { data: result, isPending: isAnalyzing } = useQuery({
    // eslint-disable-next-line @tanstack/query/exhaustive-deps
    queryKey: schemaInferenceQueryKeys.inferenceResult(queryPrefix),
    queryFn: () =>
      sheetReader.inferSchema({
        fileName,
        sheetName,
      }),
  });

  return (
    <Card>
      <CardContent>
        {isAnalyzing && <LinearProgress />}
        <Box sx={{ p: 2 }}>
          <Box sx={{ display: "flex", justifyContent: "flex-end", mb: 2 }}>
            <Button onClick={onChangeSheet}>Change Sheet?</Button>
          </Box>
          <Box>
            <Typography variant={"h6"}>Inference Result</Typography>
            <Divider sx={{ my: 2 }} />
            <SchemaInferenceResultContent
              isAnalyzing={isAnalyzing}
              result={result?.inferenceResult}
            />
          </Box>

          <Box
            sx={{ display: "flex", gap: 2, mt: 3, justifyContent: "flex-end" }}
          >
            <Button
              variant="outlined"
              color="secondary"
              onClick={paginationProps.onCancel}
              disabled={isAnalyzing}
            >
              Cancel
            </Button>
            <Button
              variant="contained"
              color="primary"
              onClick={() => paginationProps.paginate("next")}
              disabled={isAnalyzing || !result?.inferenceResult.isCompatible}
            >
              Continue
            </Button>
          </Box>

          {result && !isAnalyzing && (
            <Accordion sx={{ mt: 2 }}>
              <AccordionSummary
                expandIcon={<ExpandMoreIcon />}
                slotProps={{
                  content: {
                    sx: {
                      justifyContent: "flex-end",
                    },
                  },
                }}
              >
                Technical Details
              </AccordionSummary>
              <AccordionDetails>
                <Box sx={{ mt: 1, p: 1, bgcolor: "grey.50", borderRadius: 1 }}>
                  <Typography variant="h6" gutterBottom>
                    Schema Inference Technical Details:
                  </Typography>
                  <Typography
                    variant="body2"
                    component="pre"
                    sx={{ fontSize: "0.8rem", overflow: "auto" }}
                  >
                    {JSON.stringify(result, null, 2)}
                  </Typography>
                </Box>
              </AccordionDetails>
            </Accordion>
          )}
        </Box>
      </CardContent>
    </Card>
  );
};

export const InferenceResult = ({
  fileName,
  sheetName,
  namespace,
  paginationProps,
  onChangeSheet,
}: TSchemaInferenceResultComponentProps) => {
  if (!fileName || !sheetName) {
    return (
      <Box sx={{ p: 2 }}>
        <Typography variant="body1">
          Please select a file and sheet to analyze schema.
        </Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 2 }}>
      <SchemaInferenceResultActive
        namespace={namespace}
        fileName={fileName}
        sheetName={sheetName}
        paginationProps={paginationProps}
        onChangeSheet={onChangeSheet}
      />
    </Box>
  );
};
