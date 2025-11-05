import { SetStateAction, useCallback, useState } from "react";

type TUseLocalStorageParams<T> = {
  key: string;
  initialValue: T;
};

const useLocalStorage = <Data>(params: TUseLocalStorageParams<Data>) => {
  const { key, initialValue } = params;

  const [storedValue, setStoredValue] = useState<Data>(() => {
    try {
      const item = window.localStorage.getItem(key);
      return item ? (JSON.parse(item) as Data) : initialValue;
    } catch (error) {
      console.error(error);
      return initialValue;
    }
  });

  const setValue = useCallback(
    (value: SetStateAction<Data> | Data) => {
      setStoredValue((prev) => {
        if (typeof value === "function") {
          const newState = (value as (prev: Data) => Data)(prev);
          window.localStorage.setItem(key, JSON.stringify(newState));
          return newState;
        }
        window.localStorage.setItem(key, JSON.stringify(value));
        return value;
      });
    },
    [key],
  );

  return [storedValue, setValue] as const;
};

export default useLocalStorage;
