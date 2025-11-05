import { TUserAction } from "../domain/EngagementTasks";
import { TActionType } from "../types/TSCustomAction";

export const getActionGerund = (action: TActionType | TUserAction): string => {
  const mapping = {
    tag: "Tagging",
    extract: "Extracting",
    untag: "Untagging",
    set: "Tagging",
    unset: "Untagging",
    discover: "Discovering",
  };
  return mapping[action];
};

export const getActionPastTense = (
  action: TActionType | TUserAction,
): string => {
  const mapping = {
    tag: "Tagged",
    extract: "Extracted",
    untag: "Untagged",
    set: "Tagged",
    unset: "Untagged",
    discover: "Discovered",
  };
  return mapping[action];
};
