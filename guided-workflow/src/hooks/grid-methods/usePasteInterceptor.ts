import { TPasteEventPayload, TSelectObject } from "@datagridxl/datagridxl2";
import { useCallback, useRef } from "react";
import { ExternalToast, toast } from "sonner";

import { useMaxStackSizeDetector } from "~/hooks/grid-methods/useMaxStackSizeDetector";
import useGridRef from "~/hooks/useGridRef";

type TLargePasteCallback = (
  nRows: number,
  maxSize: number,
  truncated: boolean,
) => void;

const countRows = (text: string) => text.split("\n").length - 1;
const countCols = (text: string) => text.split("\n")[0].split("\t").length;

export const usePasteInterceptor = () => {
  /**
   * This hook integrates with DataGridXL's events to intercept paste events
   *
   * ## It returns a factory function that can accept an arbitrary callback function
   *
   * ## Behaviors:
   *
   * ### Large Paste Interceptor
   * notify the user if the paste operation is too large.
   * In this event, the paste operation is truncated to the size returned from `useMaxStackSizeDetector`, the user is informed and the grid is scrolled to the
   *   bottom of the grid and an additional blank row is added to the grid.
   *
   * Paste operations that exceed ~126,000 rows (cannot be known at runtime) run afoul of this line of code from DataGridXL:
   * ```
   * this._rows.indexList.splice.apply(this._rows.indexList, [r, 0].concat(i));
   * ```
   *
   * ### Ensure Blank Row
   * If a user pastes data into the grid, by default the grid will resize to fit the data, *exactly*. However, we want to
   * ensure that there is always a blank row at the end of the grid. We don't use a naive approach of just adding a blank row every time
   *
   */
  const maxRows = useMaxStackSizeDetector() - 1000;
  if (maxRows <= 0) {
    throw new Error("Max stack size is too small");
  }
  const largePasteCallbackRef = useRef<TLargePasteCallback | null>(null);

  const truncateInterceptorFactory = useCallback(
    (onTruncated: TLargePasteCallback) => {
      largePasteCallbackRef.current = onTruncated;
      return (event: TPasteEventPayload) => {
        const { text } = event;
        const nRows = countRows(text);
        const nCols = countCols(text);
        const blankRow = "\t".repeat(nCols) + "\r\n";

        if (nRows <= maxRows) {
          event.text += blankRow;
          largePasteCallbackRef.current?.(nRows, maxRows, false);
          return;
        }
        let seenRows = 0;
        let lastIndex = -1;

        for (let i = 0; i < text.length; i++) {
          if (text[i] === "\n") {
            seenRows++;
          }
          if (seenRows === maxRows) {
            lastIndex = i; // This is where we want to truncate
            break;
          }
        }

        if (lastIndex === -1) {
          // No rows at all
          return;
        }
        event.text = text.slice(0, lastIndex + 1);
        // Add a blank row for easy pasting
        event.text += blankRow;
        largePasteCallbackRef.current?.(nRows, maxRows, true);
      };
    },
    [maxRows],
  );

  return { interceptorFactory: truncateInterceptorFactory };
};

const defaultToastOptions = {
  duration: 15000,
};

export const usePasteInterceptorWithToast = ({
  gridRef,
  toastOptions = defaultToastOptions,
}: {
  gridRef: ReturnType<typeof useGridRef>;
  toastOptions?: ExternalToast;
}) => {
  const { interceptorFactory } = usePasteInterceptor();

  // Callback to display toast message when paste operation is truncated and scroll to bottom in DGXL

  const onTruncated = useCallback<TLargePasteCallback>(
    (nRows, maxSize, wasTruncated: boolean) => {
      if (wasTruncated)
        toast.info(
          `Your paste operation of ${nRows} rows was truncated at ${maxSize} rows to prevent the page from crashing. You may continue pasting the remaining rows at the end of the spreadsheet.`,
          toastOptions,
        );

      // Now we need to attach another event listener for setcellvalues event. Once this executes, we will scroll to the bottom
      // and then it will be removed

      const scrollToBottomAfterSetValues = (payload: {
        selection: TSelectObject[];
      }) => {
        const grid = gridRef.current?.grid;
        if (!grid) {
          console.error("Grid not found");
          return;
        }
        let minX = 0;
        let maxY = 0;
        for (let i = 0; i < payload.selection.length; i++) {
          const { range } = payload.selection[i];
          for (let j = 0; j < range.length; j++) {
            minX = Math.min(minX, range[j].x);
            maxY = Math.max(maxY, range[j].y);
          }
        }

        grid.setCellSelection({ x: minX, y: maxY });
        grid.setViewportPosition({ x: minX, y: maxY });
        grid.events.off("change", scrollToBottomAfterSetValues);
      };

      const grid = gridRef.current?.grid;
      if (!grid) {
        console.error("Grid not found");
        return;
      }
      grid.events.on("change", scrollToBottomAfterSetValues);
    },
    [gridRef, toastOptions],
  );

  const interceptor = useCallback(
    () => interceptorFactory(onTruncated),
    [interceptorFactory, onTruncated],
  );

  return { interceptor };
};
