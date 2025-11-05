import { TActionType } from "../types/TSCustomAction";
import { ICanvas } from "./Canvas";
import { TEngagement } from "./Engagement";
import { TagOption } from "./thoughtspot";

export type TUserAction = "set" | "unset" | "extract";

export type TAnswerServiceContext = {
  answerUrl: string;
  actionType: TActionType;
  vizName: string;
  type: "answerService";
  engagementId: TEngagement["dc_engagement_id"];
  canvasId: ICanvas["canvas_id"];
  warningSeverity?: string;
};

export type TTaskBase<Context = DefaultContextType> = {
  canvas_id: number;
  comment: string;
  engagement_id: number;
  context: Context;
  config_strategy: TagOption;
};

type TTagType = {
  tag_ids: number[];
  tagset_ids: number[];
  user_action: "set";
};

type TUntagType = {
  tag_ids: null;
  tagset_ids: number[];
  user_action: "unset";
};

type TExtractType = {
  tag_ids: null;
  tagset_ids: null;
  user_action: "extract";
};

type DefaultContextType = TAnswerServiceContext;

export type ITagEngagement<Context = DefaultContextType> = TTaskBase &
  TTagType & { context: Context };

export type IUntagEngagement<Context = DefaultContextType> = TTaskBase &
  TUntagType & { context: Context };

export type IExtractEngagement<Context = DefaultContextType> = TTaskBase &
  TExtractType & { context: Context };

export type TEngagementTaskSubmission<Context = DefaultContextType> =
  | ITagEngagement<Context>
  | IUntagEngagement<Context>
  | IExtractEngagement<Context>;
