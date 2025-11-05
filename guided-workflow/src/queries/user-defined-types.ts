import { getUserDefinedTypesByFieldName } from "~/api/user-defined-types";
import { TUserDefinedTypeFieldNames } from "~/domain/UserDefinedTypes";
import { userDefinedTypesQueryKeys } from "~/utils/queryKeys";

export const userDefinedTypesQuery = (request: {
  engagementId: number;
  fieldName: TUserDefinedTypeFieldNames;
}) => ({
  queryKey: userDefinedTypesQueryKeys.list(request),
  queryFn: () =>
    getUserDefinedTypesByFieldName(request.engagementId, request.fieldName),
});
