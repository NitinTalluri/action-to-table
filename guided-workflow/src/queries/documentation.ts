import { getDocumentation } from "~/api/documentation";
import { TDocumentationEnums } from "~/domain/Documentation";
import { documentationQueryKeys } from "~/utils/queryKeys";

export const documentationQuery = (id: TDocumentationEnums) => ({
  queryKey: documentationQueryKeys.detail(id),
  queryFn: () => getDocumentation(id),
  retry: false,
});
