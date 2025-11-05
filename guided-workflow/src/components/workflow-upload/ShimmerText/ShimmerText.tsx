import { TypographyProps } from "@mui/material";
import Typography from "@mui/material/Typography";
import { motion } from "framer-motion";

interface TShimmerTextProps extends TypographyProps {
  children: React.ReactNode;
  shimmerDelay?: number;
  emergeDuration?: number;
  shimmerDuration?: number;
}

/**
 * A wrapper around MUI Typography that adds a shimmer animation effect.
 * Text emerges from below with configurable shimmer overlay animation.
 *
 * @example
 * <ShimmerText variant="h4">Perfect Match</ShimmerText>
 * <ShimmerText variant="body1" shimmerDelay={0.5}>Success!</ShimmerText>
 */

export const ShimmerText = ({
  children,
  shimmerDelay = 0,
  emergeDuration = 0.2,
  shimmerDuration = 1.5,
  sx,
  ...typographyProps
}: TShimmerTextProps) => {
  const shimmerOverlayStyle = {
    position: "absolute" as const,
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    background: `linear-gradient(100deg, 
      rgba(255, 255, 255, 0.0) 10%, 
      rgba(255, 255, 255, 0.9) 15%, 
      rgba(255, 255, 255, 0.0) 30%
    )`,
    backgroundSize: "200% 100%",
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: emergeDuration }}
      style={{ position: "relative" }}
    >
      <Typography sx={sx} {...typographyProps}>
        {children}
      </Typography>
      <motion.div
        initial={{ backgroundPosition: "100% 0" }}
        animate={{ backgroundPosition: "-100% 0" }}
        transition={{
          duration: shimmerDuration,
          ease: "easeOut",
          delay: shimmerDelay,
        }}
        style={shimmerOverlayStyle}
      />
    </motion.div>
  );
};
