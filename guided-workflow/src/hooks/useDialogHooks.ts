import { useState } from "react";

export const useDialogState = <Option>() => {
  const [dialogOpen, setDialogOpen] = useState(false);
  const [value, setValue] = useState<Option | null>(null);

  return {
    dialogOpen,
    setDialogOpen,
    value,
    setValue,
  };
};
