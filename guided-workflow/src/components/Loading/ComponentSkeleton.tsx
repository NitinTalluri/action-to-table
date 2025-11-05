import { SxProps } from "@mui/material";
import Skeleton from "@mui/material/Skeleton";
import React from "react";

type ComponentSkeletonProps = {
  sx?: SxProps;
};
const ComponentSkeleton = (props?: ComponentSkeletonProps) => {
  const { sx } = props ?? {};
  const defaultSx: SxProps = {
    height: "50vh",
    width: "100%",
    ...sx,
  };
  return <Skeleton variant={"rectangular"} sx={defaultSx} />;
};

export default ComponentSkeleton;
