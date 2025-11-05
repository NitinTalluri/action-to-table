import { useEffect, useState } from "react";

type TButtonState = {
  actionKey: string;
  lastPress: number;
};

const useDebounceButton = (
  disableTimeInSecs: number,
  actionKey: string,
): [boolean, () => void] => {
  /**
   * This hook is used to disable a button for a certain amount of time. To persist, the button must be provided a uni
   * que key.
   */

  const getButtonStateFromLocalStorage = () => {
    const buttonState = localStorage.getItem(actionKey);
    if (!buttonState) {
      return {
        actionKey: actionKey,
        lastPress: 0,
      };
    } else {
      return JSON.parse(buttonState);
    }
  };

  const setButtonStateToLocalStorage = (buttonState: TButtonState) => {
    localStorage.setItem(actionKey, JSON.stringify(buttonState));
  };

  const [buttonState, setButtonState] = useState<TButtonState>(
    getButtonStateFromLocalStorage(),
  );
  const [buttonDisabled, setButtonDisabled] = useState(
    buttonState.lastPress + disableTimeInSecs * 1000 > Date.now(),
  );

  useEffect(() => {
    if (buttonDisabled) {
      const timeoutId = setTimeout(
        () => setButtonDisabled(false),
        buttonState.lastPress + disableTimeInSecs * 1000 - Date.now(),
      );
      return () => clearTimeout(timeoutId);
    }
  }, [buttonDisabled, buttonState.lastPress, disableTimeInSecs]);

  // Button click handler
  const handleClick = () => {
    const updatedState = { ...buttonState, lastPress: Date.now() };
    setButtonState(updatedState);
    setButtonDisabled(true);
    setButtonStateToLocalStorage(updatedState);
  };

  // Return the state and handler
  return [buttonDisabled, handleClick];
};

export default useDebounceButton;
