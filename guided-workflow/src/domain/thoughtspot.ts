import { z } from "zod";

import {
  TButtonActionType,
  TTagActionExtra,
} from "~/features/thoughtspot/Dialog/Table/TagActionDetailTable";

import { IEngagementTaskAPI } from "./EngagementTasksAPI";

export type TTagActionId = "tag";
export type TExtractActionId = "extract";
export type TTagActionDialogId = TTagActionId | TExtractActionId;
export type THandleSubmit = (props: TOnSubmitProps) => void;

export const TagOptionSchema = z.union([
  z.literal("config-all"),
  z.literal("config-null"),
  z.literal(""),
  z.literal("null"),
  z.null(),
]);

export type TagOption = z.infer<typeof TagOptionSchema>;

export type TSendExtractInstanceIds = {
  idList: number[];
  columnsToExtract: TTagActionExtra;
  engagementId: number;
};

export type TCreateTagActionsPayload = {
  requests: {
    thoughtspot_id: number;
    config_strategy: TagOption;
  }[];
};

export type TTagActionOnSubmitProps = TOnSubmitBaseProps & {
  dialogType: TTagActionId;
  extra: null;
};

export type TOnSubmitBaseProps = {
  actions: IEngagementTaskAPI[];
  action: TButtonActionType;
  tagOption?: TagOption;
};

export type TExtractActionOnSubmitProps = {
  actions: IEngagementTaskAPI[];
  action: "submit";
  dialogType: TExtractActionId;
  extra: TTagActionExtra;
  tagOption?: TagOption;
};

export type TExtractActionDeleteOnSubmitProps = {
  actions: IEngagementTaskAPI[];
  action: "delete";
  dialogType: TExtractActionId;
  extra: null;
  tagOption?: TagOption;
};

export type TOnSubmitProps =
  | TTagActionOnSubmitProps
  | TExtractActionOnSubmitProps
  | TExtractActionDeleteOnSubmitProps;
