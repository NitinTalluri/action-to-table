import { useMemo } from "react";

const testStackSize = (size: number) => {
  const stack: number[] = new Array(100).fill(0);
  const incoming = new Array(size).fill(0);
  try {
    stack.splice.apply(stack, [100, 0, ...incoming]);
    return true;
  } catch (e) {
    return false;
  }
};

const maxSizeDetector = ({
  startIncrement = 1000,
  start = 1000,
  precision = 100,
}: {
  startIncrement: number;
  start: number;
  precision: number;
}) => {
  /**
   * DGXL has an upper bound on the maximum number of rows that can be allocated in the grid
   *  in a single operation. This upper bound is client specific and needs to be determined
   *  empirically.
   */

  let currentSize = start;
  let lastSuccess = 0;
  let increment = startIncrement;

  while (increment > precision) {
    const success = testStackSize(currentSize);
    if (success) {
      lastSuccess = currentSize;
      increment = (increment * 3) >> 1;
      currentSize += increment;
    } else {
      increment >>= 1;
      currentSize -= increment;
    }
  }

  return lastSuccess;
};

export const useMaxStackSizeDetector = () => {
  const maxStackSize = useMemo(() => {
    return maxSizeDetector({
      startIncrement: 1000,
      start: 1000,
      precision: 100,
    });
  }, []);
  return maxStackSize;
};
