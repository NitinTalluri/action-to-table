import { useContext } from "react";

import { IAmplifyUser } from "~/domain/Users";
import { UserContext } from "~/hooks/users/userContext";

const useUserContext = (): IAmplifyUser => {
  const context = useContext(UserContext);
  if (!context) {
    throw new Error("useUserContext must be used within a UserProvider");
  }
  const { user } = context;
  if (!user) {
    // The provider should not render children if the user is not defined
    throw new Error("User is not defined in the UserContext - Logic Error");
  }
  return user;
};

export default useUserContext;
