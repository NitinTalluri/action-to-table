import { useEffect, useRef, useState } from "react";

export const useContainerDimensions = () => {
  const ref = useRef<HTMLDivElement>(null);
  const [domRect, setDomRect] = useState<DOMRect>();

  useEffect(() => {
    if (!ref.current) return;
    const observer = new ResizeObserver((entries) => {
      for (const entry of entries) {
        setDomRect(entry.target.getBoundingClientRect());
      }
    });
    observer.observe(ref.current);
    return () => observer.disconnect();
  }, []);

  return { ref, domRect };
};
