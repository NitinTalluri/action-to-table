import { useCallback, useEffect, useRef, useState } from "react";

import { ICanvas } from "../domain/Canvas";
import { TContainerActionType } from "../features/canvas/ActionContainer/CanvasActionContainer";
import useLocalStorage from "./useLocalStorage";

type UseDebouncedActionsParams = {
  key: string;
  debounceTimeMs: number;
};

type TActionMap = {
  [canvasId: ICanvas["canvas_id"]]: {
    [actionId in TContainerActionType]?: number;
  };
};
export type TActionStates = {
  [canvasId: ICanvas["canvas_id"]]: {
    [actionId in TContainerActionType]?: boolean;
  };
};

type TUseDebouncedActions = {
  actionStates: TActionStates;
  trackAction: (
    canvasId: ICanvas["canvas_id"],
    actionId: TContainerActionType,
  ) => void;
  clearAction: (
    canvasId: ICanvas["canvas_id"],
    actionId: TContainerActionType,
  ) => void;
};

const getActionStates = (
  actionMappings: TActionMap,
  debounceTimeMs: number,
): TActionStates => {
  // Convert dateTimeMs to boolean if the action is debounced or not
  const now = Date.now();
  return Object.entries(actionMappings).reduce((acc, [canvasId, actionMap]) => {
    const canvasActionStates = Object.entries(actionMap).reduce(
      (acc, [actionId, dateTimeMs]) => {
        if (!dateTimeMs) return acc;
        const isDebounced = now - dateTimeMs < debounceTimeMs;
        return {
          ...acc,
          [actionId]: isDebounced,
        };
      },
      {},
    );
    return {
      ...acc,
      [canvasId]: canvasActionStates,
    };
  }, {});
};

const useDebouncedActions = (
  params: UseDebouncedActionsParams,
): TUseDebouncedActions => {
  /**
   useDebouncedActions

   This hook internally uses the useLocalStorage hook to store the actions in the local storage.
   The intention is that we want to maintain a map of action-id: timestamp, so we can check if the action should be debounced or not.
   */
  const { key, debounceTimeMs } = params;
  const timerIdRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [dataStore, setDataStore] = useLocalStorage<TActionMap>({
    key,
    initialValue: {},
  });
  const [actionStates, setActionStates] = useState<TActionStates>(
    getActionStates(dataStore, debounceTimeMs),
  );

  const trackAction = (
    canvasId: ICanvas["canvas_id"],
    actionId: TContainerActionType,
  ) => {
    const now = Date.now();
    const canvasData = dataStore[canvasId] ?? {};
    const newDataStore = {
      ...dataStore,
      [canvasId]: {
        ...canvasData,
        [actionId]: now,
      },
    };
    setDataStore(newDataStore);
    const newActionStates = getActionStates(newDataStore, debounceTimeMs);
    setActionStates(newActionStates);
  };

  const trackActionCb = useCallback(trackAction, [dataStore, debounceTimeMs]);

  const clearAction = (
    canvasId: ICanvas["canvas_id"],
    actionId: TContainerActionType,
  ) => {
    const canvasData = dataStore[canvasId] ?? {};
    const newDataStore = {
      ...dataStore,
      [canvasId]: {
        ...canvasData,
        [actionId]: undefined,
      },
    };
    setDataStore(newDataStore);
    const newActionStates = getActionStates(newDataStore, debounceTimeMs);
    setActionStates(newActionStates);
  };

  const clearActionCb = useCallback(clearAction, [dataStore, debounceTimeMs]);

  useEffect(() => {
    // If any action is marked as debounced, we will set a timeout to update the action states
    const hasDebouncedActions = Object.values(actionStates).some((a) => a);
    if (!hasDebouncedActions) return;
    timerIdRef.current = setTimeout(() => {
      const newActionStates = getActionStates(dataStore, debounceTimeMs);
      setActionStates(newActionStates);
    }, debounceTimeMs);
  }, [actionStates, dataStore, debounceTimeMs]);

  return {
    actionStates,
    trackAction: trackActionCb,
    clearAction: clearActionCb,
  };
};

export default useDebouncedActions;
