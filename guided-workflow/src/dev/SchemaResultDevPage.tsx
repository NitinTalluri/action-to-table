import { Box, Button, Container, Typography, TypographyProps } from "@mui/material";
import { motion } from "framer-motion";
import { useState } from "react";

interface TShimmerTextProps extends TypographyProps {
  children: React.ReactNode;
  shimmerDelay?: number;
  emergeDuration?: number;
  shimmerDuration?: number;
}

const ShimmerText = ({ 
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
      style={{ position: "relative", display: "inline-block" }}
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
          delay: shimmerDelay
        }}
        style={shimmerOverlayStyle}
      />
    </motion.div>
  );
};

export const SchemaResultDevPage = () => {
  const [animationKey, setAnimationKey] = useState(0);

  const handleReplay = () => {
    setAnimationKey(prev => prev + 1);
  };

  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Box 
        sx={{
          
          display: "flex", 
          flexDirection: "column",
          justifyContent: "center", 
          alignItems: "center", 
          minHeight: "50vh",
          gap: 4
        }}
      >
        <ShimmerText key={animationKey} variant="h4">Perfect Match</ShimmerText>
    
        <Button variant="contained" onClick={handleReplay}>
          Replay Animation
        </Button>
      </Box>
    </Container>
  );
};