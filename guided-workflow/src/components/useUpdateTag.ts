import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { updateGlobalTag, updateTag } from "~/api/tags";
import { TTag } from "~/domain/Tags";
import { TTagset } from "~/domain/Tagset";
import { getErrorMessage } from "~/utils/getErrorMessage";
import { tagsetsQueryKeys } from "~/utils/queryKeys";

export const useUpdateTag = (engagementId: number | null) => {
  const queryClient = useQueryClient();

  const updateTagMutationFn = async (tag: TTag) => {
    if (!engagementId)
      throw new Error("Engagement ID is required to update a tag");
    return await updateTag({ tagData: tag, engagementId });
  };

  const updateGlobalTagMutationFn = async (tag: TTag) =>
    await updateGlobalTag(tag);

  const { mutateAsync } = useMutation({
    mutationFn: (tag: TTag) => {
      if (!engagementId) {
        return updateGlobalTagMutationFn(tag);
      }
      return updateTagMutationFn(tag);
    },
    onMutate: (data) => {
      queryClient.setQueryData(
        tagsetsQueryKeys.list(engagementId || 1),
        (prevTagsets: TTagset[] | undefined) => {
          const tagsetIndex = prevTagsets?.findIndex(
            (tagset) => tagset.tagset_id === data.tagset_id,
          );
          if (tagsetIndex === -1 || typeof tagsetIndex !== "number")
            return prevTagsets;
          const tagIndex = prevTagsets?.[tagsetIndex].tags.findIndex(
            (tag) => tag.tag_id === data.tag_id,
          );
          if (tagIndex === -1 || typeof tagIndex !== "number")
            return prevTagsets;
          const newTagsets =
            prevTagsets?.map((tagset, i) => {
              if (i === tagsetIndex) {
                return {
                  ...tagset,
                  tags: tagset.tags.map((tag, j) => {
                    if (j === tagIndex) {
                      return data;
                    }
                    return tag;
                  }),
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

  const onUpdateTag = async (tag: TTag) => {
    toast.promise(mutateAsync(tag), {
      loading: "Updating tag...",
      success: "Tag updated",
      error: (error) => getErrorMessage("Failed to update tag", error),
    });
  };

  return onUpdateTag;
};
