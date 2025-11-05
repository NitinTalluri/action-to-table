import { createContext, useContext } from "react";

import { TSchemaInferenceNamespace } from "~/domain/resolvers/schemaInferenceRegistry";
import { TColumnSheetReaderFunctions } from "~/hooks/upload/useExcelReader/useColumnSheetReader";
import { TSchemaSheetReaderFunctions } from "~/hooks/upload/useExcelReader/useSchemaSheetReader";

export const ColumnSheetReaderContext =
  createContext<TColumnSheetReaderFunctions | null>(null);

export const SchemaSheetReaderContext =
  createContext<TSchemaSheetReaderFunctions | null>(null);

export const useSheetReaderColumnContext = () => {
  const context = useContext(ColumnSheetReaderContext);
  if (!context) {
    throw new Error(
      "useSheetReaderColumnContext must be used within a ColumnSheetReaderContext.Provider",
    );
  }
  return context;
};

export const useSheetReaderSchemaContext = <
  N extends TSchemaInferenceNamespace,
>({
  namespace,
}: {
  namespace: N;
}) => {
  const context = useContext(SchemaSheetReaderContext);
  if (!context) {
    throw new Error(
      "useSheetReaderSchemaContext must be used within a SchemaSheetReaderContext.Provider",
    );
  }
  if (context.namespace !== namespace) {
    throw new Error(
      `useSheetReaderSchemaContext expected namespace ${namespace} but got ${context.namespace}`,
    );
  }
  return context as TSchemaSheetReaderFunctions<N>;
};
