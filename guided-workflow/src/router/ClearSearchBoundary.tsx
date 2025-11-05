import { useEffect } from "react";
import { useRouteError, useSearchParams } from "react-router";

export const ClearSearchBoundary = () => {
  // If this renders, it just clears the search parameters
  useRouteError();
  const [, setSearchParams] = useSearchParams();

  useEffect(() => {
    setSearchParams();
  }, [setSearchParams]);

  return null;
};
