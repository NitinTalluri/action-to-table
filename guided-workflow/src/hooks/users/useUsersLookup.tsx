import { useQuery } from "@tanstack/react-query";

import { IUser } from "~/domain/Users";
import { getEngagementsUsersQuery } from "~/queries/engagements";

export const useUsersLookup = (): Record<number, IUser> | undefined => {
  const { data } = useQuery({
    queryKey: getEngagementsUsersQuery.queryKey,
    queryFn: getEngagementsUsersQuery.queryFn,
    staleTime: getEngagementsUsersQuery.staleTime,
    select: (data) =>
      data?.reduce((acc, user) => ({ ...acc, [user.user_id]: user }), {}),
  });

  return data;
};
