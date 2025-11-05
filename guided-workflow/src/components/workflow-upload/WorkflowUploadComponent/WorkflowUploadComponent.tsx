import Box from "@mui/material/Box";
import Paper from "@mui/material/Paper";

import {
  ISupportsLoadWorkbook,
  useWorkbookLoader,
} from "~/components/workflow-upload/hooks/useWorkbookLoader";
import {
  csvFileExt,
  csvFileType,
  excelFileExt,
  excelFileType,
  excelMacroFileExt,
  excelMacroFileType,
  UploadBox,
} from "~/components/workflow-upload/UploadBox";
import { SheetPicker } from "~/components/workflow-upload/WorkflowUploadComponent/SheetPicker";
import { schemaInferenceQueryKeys } from "~/domain/resolvers/schemaInferenceQueryKeys";
import { TSchemaInferenceNamespace } from "~/domain/resolvers/schemaInferenceRegistry";
import {
  TColumnMode,
  TSchemaMode,
} from "~/hooks/upload/useExcelReader/sheetReaderTypes";
import invariant from "~/utils/invariant";
import { macdHistoricalQueryKeys } from "~/utils/queryKeys";

const allowedFileTypes = [
  csvFileExt,
  csvFileType,
  excelFileExt,
  excelFileType,
  excelMacroFileExt,
  excelMacroFileType,
] as const;

export type TPaginationProps = {
  paginate: (direction: "next" | "back") => void;
  activeStep: number;
  setActiveStep: (step: number) => void;
  onCancel: () => void;
};

type TWorkflowUploadComponentPropsBase = {
  paginationProps: TPaginationProps;
  fileName: string | null;
  setFileName: (name: string | null) => void;
  sheetName: string | null;
  setSheetName: (name: string | null) => void;
};

interface ISheetReaderProtocol extends ISupportsLoadWorkbook {
  getSheets: (params: {
    fileName: string;
  }) => Promise<{ fileName: string; sheetNames: string[] }>;
}
type TWorkflowUploadColumnProps = TWorkflowUploadComponentPropsBase & {
  mode: TColumnMode;
  sheetReader: ISheetReaderProtocol;
};

type TWorkflowUploadSchemaProps = TWorkflowUploadComponentPropsBase & {
  mode: TSchemaMode;
  namespace: TSchemaInferenceNamespace;
  sheetReader: ISheetReaderProtocol;
};

type TWorkflowUploadComponentProps =
  | TWorkflowUploadColumnProps
  | TWorkflowUploadSchemaProps;

export const WorkflowUploadComponent = (
  props: TWorkflowUploadComponentProps,
) => {
  const {
    paginationProps: { paginate, onCancel },
    fileName,
    sheetName,
    setFileName,
    setSheetName,
    mode,
    sheetReader,
  } = props;

  const { handleFileDrop, handleFileDropRejected, isLoading } =
    useWorkbookLoader({ sheetReader });

  const onSheetSelect = (name: string) => {
    setSheetName(name);
    paginate("next");
  };

  const onFileDrop = async (file: File) => {
    await handleFileDrop(file, setFileName);
  };

  const onFileDropRejected = (msg: string) => {
    handleFileDropRejected(msg);
    setFileName(null);
  };

  const makeQueryKey = () => {
    invariant(fileName, "File name must be defined to make query key");
    if (mode === "schema_inference") {
      return schemaInferenceQueryKeys.list(props.namespace, fileName);
    } else if (mode === "column") {
      return macdHistoricalQueryKeys.list(fileName) as readonly string[];
    } else {
      throw new Error(`Unsupported mode: ${mode}`);
    }
  };

  if (!fileName) {
    return (
      <Box sx={{ height: "100%", p: 2 }}>
        <Paper>
          <UploadBox
            onFileDrop={onFileDrop}
            allowedFileTypes={allowedFileTypes}
            loading={isLoading}
            onFileDropRejected={onFileDropRejected}
          />
        </Paper>
      </Box>
    );
  }

  if (!sheetName && fileName) {
    return (
      <Box sx={{ height: "100%", p: 2 }}>
        <Paper>
          <SheetPicker
            onCancel={onCancel}
            fileName={fileName}
            setSheetName={onSheetSelect}
            queryKey={makeQueryKey()}
            sheetReader={sheetReader}
          />
        </Paper>
      </Box>
    );
  }

  return (
    <Box sx={{ height: "100%", p: 2 }}>
      <Paper></Paper>
    </Box>
  );
};
