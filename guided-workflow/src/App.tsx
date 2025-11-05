import { usePrefetchQuery } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import { useMemo } from "react";
import { RouterProvider } from "react-router";

import { DcTypesProvider } from "~/hooks/dcTypes/useDcTypes";
import useAuthUser from "~/hooks/users/useAuthUser";
import { UserContext } from "~/hooks/users/userContext";

import LoadingSpinnerFullPage from "./components/Loading/LoadingSpinnerFullPage";
import { getGlobalTagsetsQuery } from "./queries/tagsets";
import { router } from "./router";

type AuthenticatedAppProps = Pick<
  ReturnType<typeof useAuthUser>,
  "user" | "setUser"
>;

function AuthenticatedApp({ user, setUser }: AuthenticatedAppProps) {
  usePrefetchQuery(getGlobalTagsetsQuery);

  const userContextValue = useMemo(() => ({ user, setUser }), [user, setUser]);

  return (
    <UserContext.Provider value={userContextValue}>
      <DcTypesProvider>
        <RouterProvider router={router()} />
        <ReactQueryDevtools initialIsOpen={false} />
      </DcTypesProvider>
    </UserContext.Provider>
  );
}

function App() {
  const { user, setUser, isLoading: isLoadingUser } = useAuthUser();

  if (isLoadingUser || !user) {
    return <LoadingSpinnerFullPage />;
  }

  return <AuthenticatedApp user={user} setUser={setUser} />;
}

export default App;
