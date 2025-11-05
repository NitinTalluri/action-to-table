import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { deleteGlobalTag, deleteTag } from "~/api/tags";
import { TTagset } from "~/domain/Tagset";
import { getErrorMessage } from "~/utils/getErrorMessage";
import { tagsetsQueryKeys } from "~/utils/queryKeys";

export const useDeleteTag = (engagementId: number | null) => {
  const queryClient = useQueryClient();

  const deleteTagMutationFn = async (tagId: number) => {
    if (!engagementId)
      throw new Error("Engagement ID is required to delete a tag");
    return await deleteTag(tagId);
  };

  const deleteGlobalTagMutationFn = async (tagId: number) => {
    return await deleteGlobalTag(tagId);
  };

  const { mutateAsync } = useMutation({
    mutationFn: (tagId: number) => {
      if (!engagementId) {
        return deleteGlobalTagMutationFn(tagId);
      }
      return deleteTagMutationFn(tagId);
    },
    onMutate: (tagId) => {
      queryClient.setQueryData(
        tagsetsQueryKeys.list(engagementId || 1),
        (prevTagsets: TTagset[] | undefined) => {
          const tagsetIndex = prevTagsets?.findIndex((tagset) =>
            tagset.tags.some((tag) => tag.tag_id === tagId),
          );
          if (tagsetIndex === -1 || typeof tagsetIndex !== "number")
            return prevTagsets;
          const newTagsets =
            prevTagsets?.map((tagset, i) => {
              if (i === tagsetIndex) {
                return {
                  ...tagset,
                  tags: tagset.tags.filter((tag) => tag.tag_id !== tagId),
                };
              }
              return tagset;
            }) || [];
          return newTagsets;
        },
      );
    },
    onSettled: () => {
      queryClient.invalidateQueries({
        queryKey: tagsetsQueryKeys.list(engagementId || 1),
      });
    },
  });

  const onDeleteTag = async (tagId: number) => {
    toast.promise(mutateAsync(tagId), {
      loading: "Deleting tag...",
      success: "Tag deleted",
      error: (error) => getErrorMessage("Failed to delete tag", error),
    });
  };

  return onDeleteTag;
};
