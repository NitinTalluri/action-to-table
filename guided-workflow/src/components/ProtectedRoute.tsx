import { Box } from "@mui/material";
import React from "react";
import { Outlet } from "react-router";

import { IUserCognitoGroups } from "~/domain/Users";
import useUserContext from "~/hooks/users/useUserContext";

import LoadingSpinnerFullPage from "./Loading/LoadingSpinnerFullPage";
import { NotFound } from "./not-found";

type ProtectedRouteProps = {
  allowedRoles: Array<keyof IUserCognitoGroups> | [];
};

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ allowedRoles }) => {
  const user = useUserContext();

  if (!user) {
    return <LoadingSpinnerFullPage />;
  }

  if (
    allowedRoles.length &&
    !user.isAdmin &&
    !allowedRoles.some((role) => user[role])
  ) {
    return (
      <Box sx={{ height: "100vh" }}>
        <NotFound />
      </Box>
    );
  }

  return <Outlet />;
};

export default ProtectedRoute;
