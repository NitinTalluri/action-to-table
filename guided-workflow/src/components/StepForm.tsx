import { Step, StepContent, StepLabel, Stepper } from "@mui/material";
import { ReactNode } from "react";

import invariant from "~/utils/invariant";

export type StepItem = {
  id: string;
  label: string;
};

type StepFormProps = {
  orientation?: "vertical" | "horizontal";
  activeStep: number;
  steps: StepItem[];
  children: ReactNode[];
};

const StepForm = ({
  orientation = "vertical",
  activeStep,
  steps,
  children,
}: StepFormProps) => {
  invariant(
    steps.length === children.length,
    "The number of steps does not match the number of children. Please ensure that 'steps' and 'children' arrays have the same length.",
  );

  return (
    <Stepper
      component={"div"}
      activeStep={activeStep}
      orientation={orientation}
      sx={{ flexGrow: 1, overflow: "auto", padding: 1 }}
    >
      {steps.map((step, index) => {
        return (
          <Step key={index + "-" + step.id}>
            <StepLabel>{step.label}</StepLabel>
            <StepContent
              slotProps={{
                transition: { unmountOnExit: false },
              }}
            >
              {children[index]}
            </StepContent>
          </Step>
        );
      })}
    </Stepper>
  );
};

export default StepForm;
