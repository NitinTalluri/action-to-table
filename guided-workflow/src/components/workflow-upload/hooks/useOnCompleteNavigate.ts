import { useCallback, useState } from "react";
import { useNavigate } from "react-router";

type TOnCompleteNavigateProps = {
  destination: string;
};

/**
 * Custom hook that will redirect to a specified destination once the `complete` state is set to true.
 *
 * @param props
 */

export const useOnCompleteNavigate = (props: TOnCompleteNavigateProps) => {
  const [complete, setComplete] = useState<boolean>(false);
  const navigate = useNavigate();

  const onComplete = useCallback(
    (proceed: boolean) => {
      if (proceed) {
        navigate(props.destination);
      }
      setComplete(false);
    },
    [navigate, props.destination],
  );

  return { complete, setComplete, onComplete };
};
