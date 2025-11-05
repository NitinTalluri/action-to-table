import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  createUserDefinedType,
  deleteUserDefinedType,
  editUserDefinedType,
} from "~/api/user-defined-types";
import { userDefinedTypesQuery } from "~/queries/user-defined-types";

type TUDTHookProps = {
  engagementId: number;
  fieldName: Parameters<typeof userDefinedTypesQuery>[0]["fieldName"];
};

export const useUDTOptions = (props: TUDTHookProps) => {
  const { engagementId, fieldName } = props;
  const udtQuery = userDefinedTypesQuery({
    engagementId,
    fieldName,
  });
  const queryClient = useQueryClient();
  const { data: fieldOptions, isLoading: optionsLoading } = useQuery(udtQuery);

  const { mutateAsync: createUdtOption, isPending: createUdtPending } =
    useMutation({
      mutationFn: createUserDefinedType,
      onMutate: async () => {
        await queryClient.cancelQueries({ queryKey: udtQuery.queryKey });
      },
      onSuccess: (result) => {
        queryClient.invalidateQueries({ queryKey: udtQuery.queryKey });
        return result;
      },
    });

  const { mutateAsync: deleteUdtOption, isPending: deleteUdtPending } =
    useMutation({
      mutationFn: deleteUserDefinedType,
      onMutate: async (data) => {
        queryClient.setQueryData(
          udtQuery.queryKey,
          (prevOptions: typeof fieldOptions) => {
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

  const { mutateAsync: editUdtOption, isPending: editUdtPending } = useMutation(
    {
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
    },
  );

  return {
    fieldOptions,
    optionsLoading,
    createUdtOption,
    createUdtPending,
    editUdtOption,
    editUdtPending,
    deleteUdtOption,
    deleteUdtPending,
  };
};
