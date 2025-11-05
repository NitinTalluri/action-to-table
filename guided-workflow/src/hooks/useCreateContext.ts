import { createContext, useContext } from "react";

export function createGenericContext<T>() {
  const Context = createContext<T | undefined>(undefined);

  const useGenericContext = () => {
    const context = useContext(Context);
    if (!context) {
      throw new Error("useGenericContext must be used within its Provider");
    }
    return context;
  };

  return [Context.Provider, useGenericContext] as const;
}
