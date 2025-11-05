import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { updateGlobalTagset, updateTagset } from "~/api/tagset";
import { TTagsetEngagement, TTagsetGlobal } from "~/domain/Tagset";
import { getErrorMessage } from "~/utils/getErrorMessage";
import { tagsetsQueryKeys } from "~/utils/queryKeys";

export const useUpdateTagset = (engagementId?: number) => {
  const queryClient = useQueryClient();

  const { mutateAsync, isPending } = useMutation({
    mutationFn: async (tagset: TTagsetEngagement | TTagsetGlobal) => {
      const isEngagement = tagset.scope === "Engagement";
      if (isEngagement) {
        return updateTagset(tagset);
      }
      return updateGlobalTagset(tagset);
    },
    onMutate: (data) => {
      // seed the query cache for optimistic update
      queryClient.setQueryData(
        tagsetsQueryKeys.list(engagementId || 1),
        (old: (TTagsetEngagement | TTagsetGlobal)[] | undefined) => {
          if (!old) return [];
          return old.map((tagset) => {
            if (tagset.tagset_id === data?.tagset_id) {
              return {
                ...tagset,
                ...data,
                scope: tagset.scope,
              };
            }
            return tagset;
          });
        },
      );
    },
    onSettled: () => {
      queryClient.invalidateQueries({
        queryKey: tagsetsQueryKeys.list(engagementId || 1),
      });
    },
  });

  const onUpdateTagset = async (data: TTagsetEngagement | TTagsetGlobal) => {
    toast.promise(mutateAsync(data), {
      loading: "Updating tagset...",
      success: "Tagset updated!",
      error: (error) => getErrorMessage("Failed to update tagset", error),
    });
  };

  return { onUpdateTagset, isPending };
};
