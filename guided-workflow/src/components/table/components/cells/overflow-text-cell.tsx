import { Tooltip } from "@mui/material";
import { useEffect, useRef, useState } from "react";

const cellPadding = 34;

export const OverflowTextCell = ({
  children,
  width,
}: {
  children: string;
  width: number;
}) => {
  const [isOverflown, setIsOverflown] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!ref.current) return;
    setIsOverflown(width - cellPadding < ref.current.scrollWidth);
  }, [ref, width]);

  return (
    <Tooltip
      title={isOverflown ? children : ""}
      arrow
      slotProps={{
        tooltip: {
          sx: {
            fontSize: ".85rem",
          },
        },
      }}
    >
      <div
        ref={ref}
        style={{
          // border: isOverflown ? "1px solid red" : "none",
          whiteSpace: "nowrap",
          overflow: "hidden",
          textOverflow: "ellipsis",
        }}
      >
        {children}
      </div>
    </Tooltip>
  );
};
