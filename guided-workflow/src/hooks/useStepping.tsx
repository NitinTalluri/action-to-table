import { useCallback, useState } from "react";

type TStepPagination = {
  totalSteps: number;
};

export const useStepping = (props: TStepPagination) => {
  const { totalSteps } = props;
  const [activeStep, setActiveStep] = useState<number>(0);

  const paginate = useCallback(
    (direction: "next" | "back", amount: number = 1) => {
      switch (direction) {
        case "next":
          setActiveStep((prev) => Math.min(prev + amount, totalSteps - 1));
          break;
        case "back":
          setActiveStep((prev) => Math.max(prev - amount, 0));
          break;
      }
    },
    [totalSteps],
  );

  return {
    activeStep,
    setActiveStep,
    paginate,
    isLastStep: activeStep === totalSteps - 1,
  };
};
