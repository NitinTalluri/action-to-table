import { useQuery } from "@tanstack/react-query";
import { useEffect } from "react";

import ComponentSkeleton from "~/components/Loading/ComponentSkeleton";
import { SheetSelectDialog } from "~/components/workflow-upload";

type TSheetPickerProps = {
  fileName: string;
  setSheetName: (name: string) => void;
  onCancel: () => void;
  queryKey: readonly string[];
  sheetReader: ISupportsGetSheets;
};

interface ISupportsGetSheets {
  getSheets: (params: {
    fileName: string;
  }) => Promise<{ sheetNames: string[] }>;
}

/**
 * Works with the Schema Inference Mode exclusively
 * - if multiple sheets are present, prompts user to select one
 * - if only one sheet is present, auto-selects it
 * - if no sheets are present, shows an error (should not happen with valid files)
 * - To work with column and schema inference, we only need to handle the differences in query key construction
 *
 * - Rather than useEffect to initiate useMutation, we use useQuery to fetch sheet names and allow queryKey to manage caching and refetching.
 * - This only works when fileName is non-null.
 */
export const SheetPicker = (props: TSheetPickerProps) => {
  const { fileName, setSheetName, onCancel, queryKey, sheetReader } = props;

  const { data: data, isLoading: isSheetNamesLoading } = useQuery({
    // eslint-disable-next-line @tanstack/query/exhaustive-deps
    queryKey,
    queryFn: async () => sheetReader.getSheets({ fileName }),
  });

  useEffect(() => {
    if (data?.sheetNames && data.sheetNames.length === 1) {
      setSheetName(data.sheetNames[0]);
    }
  }, [data, setSheetName]);

  if (isSheetNamesLoading) {
    return <ComponentSkeleton sx={{ height: "20vh", width: "100%" }} />;
  }

  if (!data?.sheetNames) {
    return <div>No sheets available.</div>; // Should not happen if file is valid
  }

  if (data.sheetNames.length > 1) {
    return (
      <SheetSelectDialog
        open={true}
        fileName={fileName}
        handleSheetSelect={setSheetName}
        sheetNames={data.sheetNames}
        handleClose={onCancel}
      />
    );
  }
};
