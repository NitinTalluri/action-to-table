import { useCallback } from "react";

const fontFamily = "Arial";
const fontSize = "16px";

export const useCharacterWidths = () => {
  /**
   * Hook that creates a canvas element and gets the width of a text string based on DataGridXL font size and font family
   * This is used to recreate the 'AutoFit' feature in Excel.
   * This could be more efficient, however, each call is about ~0.01ms
   */
  const getWidth = useCallback((text: string) => {
    const canvas = document.createElement("canvas");
    const context = canvas.getContext("2d");
    if (!context) {
      console.log("Canvas context not available");
      return 125;
    }
    context.font = `${fontSize} ${fontFamily} normal`;
    context.textAlign = "left";
    context.textRendering = "geometricPrecision";
    const width = context.measureText(text).width;

    return width;
  }, []);

  return getWidth;
};
