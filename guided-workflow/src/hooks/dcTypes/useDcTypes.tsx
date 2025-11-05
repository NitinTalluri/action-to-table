import { useQuery } from "@tanstack/react-query";
import {
  createContext,
  FC,
  PropsWithChildren,
  useContext,
  useMemo,
} from "react";

import LoadingSpinnerFullPage from "~/components/Loading/LoadingSpinnerFullPage";
import { TDcTypes } from "~/domain/DcTypes/schema";
import { getDcTypesQuery } from "~/queries/dcTypes";

interface IDcTypesContext {
  dcTypes: TDcTypes;
}

const DcTypesContext = createContext<IDcTypesContext | null>(null);

const DcTypesProvider: FC<PropsWithChildren> = ({ children }) => {
  // Provides the dcTypes to the application

  const { data: dcTypes, isLoading } = useQuery({
    queryKey: getDcTypesQuery.queryKey,
    queryFn: getDcTypesQuery.queryFn,
    refetchOnMount: false,
    refetchOnWindowFocus: false,
    staleTime: 12 * 60 * 60 * 1000, // 12 hour stale time
    // This is go-no-go for the app. If the server is slow to come up, we want to allow for it to come up before we give up.
    retry: true,
    // 2000, 4000, 8000, 16000, ... up to 60 seconds
    retryDelay: (attempt) => Math.min(1000 * 2 ** attempt, 60000),
  });

  const memoizedDcTypes = useMemo(() => {
    if (!dcTypes) {
      return null;
    }
    return { dcTypes };
  }, [dcTypes]);

  if (isLoading || !dcTypes || !memoizedDcTypes) {
    return <LoadingSpinnerFullPage />;
  }

  return (
    <DcTypesContext.Provider value={memoizedDcTypes}>
      {children}
    </DcTypesContext.Provider>
  );
};

const useDcTypes = (): TDcTypes => {
  const context = useContext(DcTypesContext);
  if (!context) {
    throw new Error("useDcTypes must be used within a DcTypesProvider");
  }
  const { dcTypes } = context;
  if (!dcTypes) {
    throw new Error("DC Types are not available - logic error");
  }
  return dcTypes;
};

export { DcTypesProvider, useDcTypes };
