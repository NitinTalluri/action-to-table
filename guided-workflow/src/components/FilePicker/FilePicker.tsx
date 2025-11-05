import type React from "react";
import { useRef } from "react";
import Button from "@mui/material/Button";

interface IFilePickerComponentProps {
  onFileChange: (file: File) => void;
}

export const FilePickerComponent: React.FC<IFilePickerComponentProps> = ({
  onFileChange,
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleButtonClick = (): void => {
    fileInputRef.current?.click();
  };

  const handleFileChange = (
    event: React.ChangeEvent<HTMLInputElement>,
  ): void => {
    const file = event.target.files?.[0];
    if (file) {
      onFileChange(file);
    }
  };

  return (
    <div>
      <input
        type="file"
        ref={fileInputRef}
        style={{ display: "none" }}
        onChange={handleFileChange}
        accept=".xlsx, .xls"
      />
      <Button variant="contained" onClick={handleButtonClick}>
        Open File Picker
      </Button>
    </div>
  );
};
