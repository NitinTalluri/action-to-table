import { useMutation } from "@tanstack/react-query";
import { toast } from "sonner";

export interface ISupportsLoadWorkbook {
  loadWorkbook: (file: File) => Promise<{ fileName: string }>;
}

type TUseWorkbookLoaderProps = {
  sheetReader: ISupportsLoadWorkbook;
};

/**
 * Generic workbook loading logic for workflow upload components.
 * Handles file upload, loading state, and error handling.
 */
export const useWorkbookLoader = (props: TUseWorkbookLoaderProps) => {
  const { sheetReader } = props;

  const { mutateAsync: loadWorkbookMutation, isPending: isLoading } =
    useMutation({
      mutationFn: async (file: File) => {
        const result = await sheetReader.loadWorkbook(file);
        return result.fileName;
      },
      onError: (error) => {
        toast.error(`Failed to load workbook: ${error.message}`);
      },
    });

  const handleFileDrop = async (
    file: File,
    onSuccess: (fileName: string) => void,
  ) => {
    const fileName = await loadWorkbookMutation(file);
    onSuccess(fileName);
  };

  const handleFileDropRejected = (message: string) => {
    toast.error(message);
  };

  return {
    loadWorkbook: loadWorkbookMutation,
    isLoading,
    handleFileDrop,
    handleFileDropRejected,
  };
};
