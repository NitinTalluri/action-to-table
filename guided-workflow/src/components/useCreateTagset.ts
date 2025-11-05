import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { createGlobalTags, createTags } from "~/api/tags";
import { createGlobalTagset, createTagset } from "~/api/tagset";
import { TTagset, TTagsetEngagement, TTagsetGlobal } from "~/domain/Tagset";
import { getErrorMessage } from "~/utils/getErrorMessage";
import { tagsetsQueryKeys } from "~/utils/queryKeys";

export const useCreateTagset = (engagementId?: number) => {
  const queryClient = useQueryClient();

  const createTagsetMutationFn = async (tagset: TTagsetEngagement) => {
    const tagsetResponse = await createTagset(tagset);
    if (!tagsetResponse) throw new Error("Failed to create tagset");
    await createTags({
      tags: tagset.tags.map((tag) => ({
        ...tag,
        tagset_id: tagsetResponse.tagset_id,
      })),
      engagementId: tagset.dc_engagement_id,
    });
  };

  const createGlobalTagsetMutationFn = async (tagset: TTagsetGlobal) => {
    const tagsetResponse = await createGlobalTagset(tagset);
    if (!tagsetResponse) throw new Error("Failed to create global tagset");
    await createGlobalTags(
      tagset.tags.map((tag) => ({
        ...tag,
        tagset_id: tagsetResponse.tagset_id,
      })),
    );
  };

  const { mutateAsync } = useMutation({
    mutationFn: (tagset: TTagset) => {
      if (tagset.scope === "Global") {
        return createGlobalTagsetMutationFn(tagset);
      }
      return createTagsetMutationFn(tagset);
    },
    onSettled: async () => {
      await queryClient.invalidateQueries({
        queryKey: tagsetsQueryKeys.list(engagementId || 1),
      });
    },
  });

  const onCreateTagset = async (data: TTagset, onSuccess: () => void) => {
    toast.promise(mutateAsync(data), {
      loading: "Creating tagset...",
      success: () => {
        onSuccess();
        return "Tagset created!";
      },
      error: (error) => getErrorMessage("Failed to create tagset", error),
    });
  };

  return onCreateTagset;
};
