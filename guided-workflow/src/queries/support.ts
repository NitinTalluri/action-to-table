import {
  getSprintGoals,
  getSupportAgentCase,
  getSupportAgentCases,
  getSupportAvailableAgents,
  getSupportCases,
} from "~/api/support";
import { TCaseListAgentFilters } from "~/domain/Support";
import {
  sprintGoalsQueryKeys,
  supportAgentCasesQueryKeys,
  supportAvailableAgentsQueryKeys,
  supportCasesQueryKeys,
} from "~/utils/queryKeys";

export const supportCasesQuery = {
  queryKey: supportCasesQueryKeys.lists(),
  queryFn: getSupportCases,
};

export const supportAgentCasesQuery = (
  filters: Partial<TCaseListAgentFilters>,
) => ({
  queryKey: supportAgentCasesQueryKeys.list(filters),
  queryFn: () => getSupportAgentCases(filters),
});

export const supportAgentCaseQuery = (caseId: number) => ({
  queryKey: supportAgentCasesQueryKeys.detail(caseId),
  queryFn: () => getSupportAgentCase(caseId),
});

export const supportAvailableAgentsQuery = {
  queryKey: supportAvailableAgentsQueryKeys.lists(),
  queryFn: getSupportAvailableAgents,
};

export const sprintGoalsQuery = () => ({
  queryKey: sprintGoalsQueryKeys.lists(),
  queryFn: getSprintGoals,
  staleTime: 24 * 60 * 60 * 1000, // 24 hours
  gcTime: 25 * 60 * 60 * 1000, // 25 hours (slightly longer than stale time)
});
