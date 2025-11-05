import { getTml } from "~/api/tml";
import { TFetchTmlProps } from "~/domain/Tml";
import { tmlQueryKeys } from "~/utils/queryKeys";

export const tmlQuery = (payload: TFetchTmlProps) => ({
  queryKey: tmlQueryKeys.detail(payload),
  queryFn: () => getTml(payload),
});
