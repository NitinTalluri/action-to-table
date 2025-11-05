import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  createUserDefinedType,
  deleteUserDefinedType,
  editUserDefinedType,
} from "~/api/user-defined-types";
import { TUserDefinedTypeFieldNames } from "~/domain/UserDefinedTypes";
import { userDefinedTypesQuery } from "~/queries/user-defined-types";

export const useUserDefinedTypes = ({
  engagementId,
  fieldName,
}: {
  engagementId: number;
  fieldName: TUserDefinedTypeFieldNames;
}) => {
  const udtQuery = userDefinedTypesQuery({
    engagementId,
    fieldName,
  });

  const queryClient = useQueryClient();
  const { data: userDefinedTypes, isLoading: userDefinedTypesLoading } =
    useQuery(udtQuery);

  const createUdtMutation = useMutation({
    mutationFn: createUserDefinedType,
    onMutate: async () => {
      await queryClient.cancelQueries({ queryKey: udtQuery.queryKey });
    },
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: udtQuery.queryKey });
      return result;
    },
  });

  const deleteUdtMutation = useMutation({
    mutationFn: deleteUserDefinedType,
    onMutate: async (data) => {
      queryClient.setQueryData(
        udtQuery.queryKey,
        (prevOptions: typeof userDefinedTypes) => {
          if (!prevOptions) {
            return prevOptions;
          }
          return [...prevOptions.filter((o) => o.id !== data.id)];
        },
      );
      await queryClient.cancelQueries({ queryKey: udtQuery.queryKey });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: udtQuery.queryKey });
    },
  });

  const editUdtMutation = useMutation({
    mutationFn: editUserDefinedType,
    onMutate: async () => {
      // Cancel any outgoing refetches
      // (so they don't overwrite our optimistic update)
      await queryClient.cancelQueries({ queryKey: udtQuery.queryKey });
    },
    onSuccess: async () => {
      // Rarely, the id of the edited option will change
      await queryClient.invalidateQueries({ queryKey: udtQuery.queryKey });
    },
  });

  return {
    userDefinedTypes,
    userDefinedTypesLoading,
    createUdtMutation,
    deleteUdtMutation,
    editUdtMutation,
  };
};
