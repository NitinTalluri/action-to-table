import { useState } from "react";

/**
 * Generic file state management for workflow upload components.
 * Manages fileName and sheetName state with reset functionality.
 */
export const useFileState = () => {
  const [fileName, setFileName] = useState<string | null>(null);
  const [sheetName, setSheetName] = useState<string | null>(null);

  return {
    fileName,
    setFileName,
    sheetName,
    setSheetName,
  };
};
