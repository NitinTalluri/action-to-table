export type TPaginationProps = {
  paginate: (direction: "next" | "back") => void;
  activeStep: number;
  setActiveStep: (step: number) => void;
  onCancel: () => void;
};
