import { useCallback } from "react";

import useLocalStorage from "~/hooks/useLocalStorage";

type TUseSelectionHistoryProps = {
  key: string;
  maxHistory?: number;
};

type TInnerDataType = {
  id: number;
  value: string;
};

type TUseSelectionHistoryReturn = [TInnerDataType[], (value: string) => void];

export const useSelectionHistory = (
  props: TUseSelectionHistoryProps,
): TUseSelectionHistoryReturn => {
  const { key, maxHistory } = props;
  const [storedValue, setStoredValue] = useLocalStorage<TInnerDataType[]>({
    key: key,
    initialValue: [
      {
        id: new Date().getTime(),
        value: "",
      },
    ],
  });

  const addSelection = useCallback(
    (value: string) => {
      const id = new Date().getTime();
      const newSelection = [
        ...storedValue.filter((sv) => sv.value !== value),
        { id, value },
      ];
      newSelection.sort((a, b) => b.id - a.id);
      if (maxHistory) {
        setStoredValue(newSelection.slice(0, maxHistory));
      } else {
        setStoredValue(newSelection);
      }
    },
    [maxHistory, setStoredValue, storedValue],
  );

  return [storedValue, addSelection];
};
