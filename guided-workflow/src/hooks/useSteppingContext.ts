import { StepContextType, useStepContext } from "@mui/material/Step";

import invariant from "~/utils/invariant";

const useSteppingContext = (): StepContextType => {
  const ctx = useStepContext();
  invariant(
    Object.keys(ctx).length > 0,
    "useSteppingContext must be used within a Stepper",
  );
  return ctx as StepContextType;
};

export default useSteppingContext;
