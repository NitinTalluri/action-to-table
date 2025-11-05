import { MutableRefObject, useEffect, useRef } from "react";

const isVisible = () => document.visibilityState === "visible";

const useVisibilityChange = (
  callback: (isVisible: boolean) => void,
): MutableRefObject<(() => void) | undefined> => {
  /**
   * This hook is used to detect when the user switches tabs or minimizes the window.
   * The callback is called with a boolean indicating if the tab is visible or not.
   */
  const eventHandle = useRef<() => void>();

  useEffect(() => {
    // Attach internal event listener to the document

    eventHandle.current = () => {
      // We've got a new visibility state
      const visible = isVisible();
      callback(visible);
    };
    document.addEventListener("visibilitychange", eventHandle.current);

    return () => {
      // Clean up the event listener when the component is unmounted
      if (eventHandle.current)
        document.removeEventListener("visibilitychange", eventHandle.current);
      eventHandle.current = undefined;
    };
  }, [callback]);

  return eventHandle;
};

export default useVisibilityChange;
