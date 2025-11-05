import { motion } from "framer-motion";
import { ReactNode } from "react";

const sequenceStepSec = 0.2;
const initialState = { opacity: 0, y: 10 };
const animateState = { opacity: 1, y: 0 };
const animationDuration = 0.4;

export const AnimateIn = ({
  children,
  sequenceNumber,
  layoutId,
}: {
  sequenceNumber: number;
  layoutId: string;
  children: ReactNode;
}) => {
  const transitionState = {
    duration: animationDuration,
    delay: sequenceStepSec * sequenceNumber,
  };
  return (
    <motion.div
      initial={initialState}
      animate={animateState}
      transition={transitionState}
      layoutId={layoutId}
    >
      {children}
    </motion.div>
  );
};

export const AnimatedHeader = ({ children }: { children: ReactNode }) => (
  <AnimateIn sequenceNumber={1} layoutId="header">
    {children}
  </AnimateIn>
);

export const AnimatedMembers = ({ children }: { children: ReactNode }) => (
  <AnimateIn sequenceNumber={2} layoutId="members">
    {children}
  </AnimateIn>
);
