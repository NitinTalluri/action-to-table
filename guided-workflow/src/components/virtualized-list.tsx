import { Box } from "@mui/material";
import { useVirtualizer } from "@tanstack/react-virtual";
import { ReactNode, useRef } from "react";

export const VirtualizedList = <T extends object>({
  items,
  keyName,
  estimateSize,
  overscan = 10,
  children,
}: {
  keyName: keyof T;
  items: T[];
  estimateSize: number;
  overscan?: number;
  children: (props: T) => ReactNode;
}) => {
  const parentRef = useRef<HTMLDivElement>(null);
  const rowVirtualizer = useVirtualizer({
    count: items.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => estimateSize,
    overscan,
  });
  const virtualizedItems = rowVirtualizer.getVirtualItems();

  return (
    <Box
      ref={parentRef}
      sx={{
        overflowY: "auto",
        height: "100%",
        backgroundColor: "grey.300",
        padding: 1,
        borderRadius: 1,
      }}
    >
      <div
        style={{
          height: `${rowVirtualizer.getTotalSize()}px`,
          width: "100%",
          position: "relative",
        }}
      >
        {virtualizedItems.map((virtualizedItem) => {
          const item = items[virtualizedItem.index];
          const key = `${virtualizedItem.key}:${item[keyName]}`;
          return (
            <div
              key={key}
              ref={rowVirtualizer.measureElement}
              data-index={virtualizedItem.index}
              style={{
                position: "absolute",
                top: 0,
                left: 0,
                width: "100%",
                transform: `translateY(${virtualizedItem.start}px)`,
              }}
            >
              {/* Render item here */}
              {children(item)}
            </div>
          );
        })}
      </div>
    </Box>
  );
};
