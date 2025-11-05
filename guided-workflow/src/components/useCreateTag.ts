import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { createGlobalTag, createTag } from "~/api/tags";
import { TTagRequest } from "~/domain/Tags";
import { getErrorMessage } from "~/utils/getErrorMessage";
import { tagsetsQueryKeys } from "~/utils/queryKeys";

export const useCreateTag = (engagementId: number | null) => {
  const queryClient = useQueryClient();

  const createTagMutationFn = async (tag: TTagRequest) => {
    if (!engagementId)
      throw new Error("Engagement ID is required to create a tag");
    return await createTag({ tagData: tag, engagementId });
  };

  const createGlobalTagMutationFn = async (tag: TTagRequest) =>
    await createGlobalTag(tag);

  const { mutateAsync, isPending } = useMutation({
    mutationFn: (tag: TTagRequest) => {
      if (!engagementId) {
        return createGlobalTagMutationFn(tag);
      }
      return createTagMutationFn(tag);
    },
    onSettled: async () => {
      await queryClient.invalidateQueries({
        queryKey: tagsetsQueryKeys.list(engagementId || 1),
      });
    },
  });

  const onCreateTag = async (tag: TTagRequest, onSuccess: () => void) => {
    toast.promise(mutateAsync(tag), {
      loading: "Creating tag...",
      success: () => {
        onSuccess();
        return "Tag created successfully";
      },
      error: (error) => getErrorMessage("Failed to create tag", error),
    });
  };

  return { onCreateTag, isPending };
};
