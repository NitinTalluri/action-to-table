import { UploadFile } from "@mui/icons-material";
import { Box, Button, Divider, Paper, Typography } from "@mui/material";
import React, { useCallback, useRef } from "react";
import { DndProvider, useDrop } from "react-dnd";
import { HTML5Backend, NativeTypes } from "react-dnd-html5-backend";

export interface DroppedFileItem {
  files: File[];
}

export interface IUploadBoxComponentProps {
  onFileDrop: (item: File) => Promise<void>;
  allowedFileTypes: readonly string[];
  loading: boolean;
  onFileDropRejected?: (message: string) => void;
}

const UploadBoxComponent = (props: IUploadBoxComponentProps) => {
  const { onFileDrop, allowedFileTypes, loading, onFileDropRejected } = props;
  const fileInputRef = useRef<HTMLInputElement>(null);
  const handleFileValidation = useCallback(
    async (file: File) => {
      const fileType = file.type;
      if (!allowedFileTypes.includes(fileType)) {
        if (onFileDropRejected) {
          onFileDropRejected(`Invalid file type: ${fileType}`);
        }
        return;
      }
      await onFileDrop(file);
    },
    [allowedFileTypes, onFileDrop, onFileDropRejected],
  );

  const handleDrop = useCallback(
    async (item: DroppedFileItem) => {
      const { files } = item;
      const file = files[0];
      await handleFileValidation(file);
    },
    [handleFileValidation],
  );

  const handleFileSelect = useCallback(
    (event: React.ChangeEvent<HTMLInputElement>) => {
      const file = event.target.files?.[0];
      if (file) {
        void handleFileValidation(file);
      }
      // Reset input value to allow selecting the same file again
      event.target.value = "";
    },
    [handleFileValidation],
  );

  const [{ canDrop, isOver }, drop] = useDrop(() => ({
    accept: [NativeTypes.FILE],
    drop: handleDrop,
    canDrop: () => !loading,
    collect: (monitor) => ({
      isOver: monitor.isOver(),
      canDrop: monitor.canDrop(),
    }),
  }));

  const isActive = canDrop && isOver;
  let borderColor = "grey";
  if (isActive) {
    borderColor = "green";
  } else if (canDrop) {
    borderColor = "blue";
  }

  // Shimmer animation for loading state
  const shimmer = loading
    ? {
        background:
          "linear-gradient(270deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%)",
        backgroundSize: "200% 100%",
        animation: "shimmer 2.5s linear infinite", // slower, left to right
        position: "relative",
      }
    : {};

  return (
    <Box
      sx={{
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        minHeight: "100%",
        p: 4,
      }}
    >
      <style>{`
                @keyframes shimmer {
                    0% { background-position: 200% 0; }
                    100% { background-position: -200% 0; }
                }
            `}</style>

      <Paper
        ref={drop}
        elevation={isActive ? 6 : 3}
        sx={{
          padding: 4,
          border: `2px dashed ${borderColor}`,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          width: "50vw",
          height: "50vh",
          textAlign: "center",
          backgroundColor: isActive ? "action.hover" : "background.paper",
          transition: "background-color 0.3s ease, border-color 0.3s ease",
          ...shimmer,
        }}
      >
        <UploadFile
          sx={{ fontSize: 60, marginBottom: 2 }}
          color={isActive ? "success" : "action"}
        />
        <Typography variant="h4" component="div" gutterBottom>
          {loading
            ? "Processing..."
            : isActive
              ? "Release to drop"
              : "Upload Excel File"}
        </Typography>
        <Typography variant="body2" color="textSecondary">
          {loading ? "Reading file, please wait..." : "Drag & drop file here"}
        </Typography>

        <Divider sx={{ width: "100%", mt: 3, mb: 2 }}>
          <Typography variant="body2" color="textSecondary">
            OR
          </Typography>
        </Divider>

        <Button
          variant="outlined"
          onClick={() => fileInputRef.current?.click()}
          disabled={loading}
        >
          Select a File
        </Button>

        <input
          type="file"
          ref={fileInputRef}
          style={{ opacity: 0 }}
          accept={`${allowedFileTypes.join(",")}`}
          onChange={handleFileSelect}
        />
      </Paper>
    </Box>
  );
};

export const UploadBox = (props: IUploadBoxComponentProps) => {
  const { onFileDrop, allowedFileTypes, loading, onFileDropRejected } = props;

  return (
    <DndProvider backend={HTML5Backend}>
      <UploadBoxComponent
        onFileDrop={onFileDrop}
        allowedFileTypes={allowedFileTypes}
        loading={loading}
        onFileDropRejected={onFileDropRejected}
      />
    </DndProvider>
  );
};
