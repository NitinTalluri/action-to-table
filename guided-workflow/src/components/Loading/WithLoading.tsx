import Skeleton, { SkeletonProps } from "@mui/material/Skeleton";
import React, { ComponentType, FC } from "react";

import LoadingSpinnerFullPage from "./LoadingSpinnerFullPage";

type TWithLoadingProps<CompParams> = {
  propKeys: (keyof CompParams)[];
  Component: ComponentType<CompParams>;
  loaderStyle?: SkeletonProps;
  fullPage?: boolean;
};

type NullableOptionalKeys<T, K extends keyof T> = {
  [P in K]?: T[P] | null;
};

const WithLoading = <CompParams extends Record<string, unknown>>(
  params: TWithLoadingProps<CompParams>,
) => {
  const { Component, propKeys, loaderStyle, fullPage } = params;
  const useFullPage = fullPage ?? false;

  const WrappedComponent: FC<
    NullableOptionalKeys<CompParams, (typeof propKeys)[number]>
  > = (props) => {
    const isAnyKeyNullish = propKeys.some(
      (key) => props[key] === null || props[key] === undefined,
    );

    if (isAnyKeyNullish && !useFullPage) {
      return <Skeleton {...loaderStyle} />;
    } else if (isAnyKeyNullish && useFullPage) {
      return <LoadingSpinnerFullPage />;
    }

    return <Component {...(props as CompParams)} />;
  };

  return WrappedComponent;
};

export default WithLoading;
