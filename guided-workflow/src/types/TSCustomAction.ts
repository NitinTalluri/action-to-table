import { AnswerService, MessagePayload } from "@thoughtspot/visual-embed-sdk";

// Id from Thoughtspot of the Action - Note these do not match the ids in the database (set, unset, extract)
export type TActionType = "tag" | "untag" | "extract" | "discover";

export interface ICustomPayload extends MessagePayload {
  data: ICustomAction;
}

export interface ICustomAnswerPayload extends ICustomPayload {
  answerService: AnswerService;
}

export const hasAnswerService = (
  p: MessagePayload,
): p is ICustomAnswerPayload => {
  return "answerService" in p && p.answerService !== undefined;
};

export interface ICustomAction {
  id: TActionType;
  contextMenuPoints: IContextMenuPoints;
  embedAnswerData: IEmbedAnswerData;
  vizId: string;
}

export interface IContextMenuPoints {
  clickedPoint: IClickedPoint;
  selectedPoints: ISelectedPoint[];
}

export interface IClickedPoint {
  selectedAttributes: IClickedPointSelectedAttribute[];
  deselectedAttributes: unknown[];
  selectedMeasures: IClickedPointSelectedMeasure[];
  deselectedMeasures: unknown[];
}

export interface IClickedPointSelectedAttribute {
  column: IXElement;
  value: string;
}

export interface IXElement {
  __typename: TColumnTypename;
  aggregationType: TAggregationType;
  baseColumnType: TBaseColumnType;
  calendarGuid: string;
  columnProps: IColumnProps;
  customCalendarType: null;
  dataType: TDataType;
  format: null;
  formatPattern: null;
  formatType: null;
  formulaId: string;
  geoConfig: null;
  id: string;
  isAdditive: boolean;
  isAggregateApplied: boolean;
  isGroupBy: boolean;
  isUserDefinedTitle: boolean;
  legacyColumnFormatProperties: null;
  legacySheetProperties: null;
  name: Name;
  referencedColumns: XReferencedColumn[];
  referencedTables: ReferencedTable[];
  showGrowth: boolean;
  timeBucket: TTimeBucket;
  type: TTSType;
}

export type TColumnTypename = "AnswerColumn";

export type TAggregationType = "NONE" | "COUNT";

export type TBaseColumnType = "SAGE_COLUMN";

export interface IColumnProps {
  __typename: TColumnPropsTypename;
  columnProperties: null;
  version: TVersion;
}

export type TColumnPropsTypename = "AnswerColumnProps";

export type TVersion = "V1";

export type TDataType = "CHAR" | "INT64" | "DATE";

type Name = string;

export interface XReferencedColumn {
  __typename: TReferencedColumnTypename;
  displayName: Name;
  guid: string;
}

export type TReferencedColumnTypename = "EntityHeader";

export interface ReferencedTable {
  __typename: TReferencedColumnTypename;
  displayName: DisplayName;
  guid: string;
}

type DisplayName = string;

export type TTimeBucket = "NO_BUCKET";

export type TTSType = "ATTRIBUTE" | "MEASURE";

export interface IClickedPointSelectedMeasure {
  column: IXElement;
  value: number;
}

export interface ISelectedPoint {
  selectedAttributes: ISelectedPointSelectedAttribute[];
  deselectedAttributes: unknown[];
  selectedMeasures: ISelectedPointSelectedMeasure[];
  deselectedMeasures: unknown[];
}

export interface ISelectedPointSelectedAttribute {
  column: IXElement;
  value: string;
}

export interface ISelectedPointSelectedMeasure {
  column: IXElement;
  value: number;
}

export interface IEmbedAnswerData {
  __typename: string;
  clientState: IClientState;
  description: string;
  filterGroups: IFilterGroup[];
  hashKey: string;
  headlineVisibilityMap: IHeadlineVisibilityMap[];
  id: string;
  name: string;
  permission: Permission;
  queryableDataSource: string;
  visualizations: Visualization[];
  columns: IEmbedAnswerDataColumn[];
  data: Datum[];
  user: User;
  reportBookMetadata: ReportBookMetadata;
  isAnswerUnsaved: boolean;
}

type IClientState = object;

export interface IEmbedAnswerDataColumn {
  __typename: string;
  column: IPurpleColumn;
}

export interface IPurpleColumn {
  __typename: TColumnTypename;
  dataType: TDataType;
  id: string;
  name: Name;
  referencedColumns: IPurpleReferencedColumn[];
  type: TTSType;
}

export interface IPurpleReferencedColumn {
  __typename: TReferencedColumnTypename;
  displayName: Name;
}

export interface Datum {
  columnDataLite: ColumnDataLite[];
  completionRatio: number;
  samplingRatio: number;
  totalRowCount: string;
}

export interface ColumnDataLite {
  columnDataType: TDataType;
  columnId: string;
  dataValue: DataValue[];
}

export type DataValue = number | null | string;

export interface IFilterGroup {
  __typename: string;
  columnInfo: IColumnInfo;
  displayName: null;
  filters: IFilter[];
  groupId: IGroupId;
  isEditable: boolean;
  isMandatory: null;
  sourceContainerId: null;
}

export interface IColumnInfo {
  __typename: string;
  aggregationType: TAggregationType;
  calendarGuid: string;
  dataType: TDataType;
  formulaId: string;
  isAggregateApplied: boolean;
  name: string;
  referencedColumns: IColumnInfoReferencedColumn[];
  referencedTables: ReferencedTable[];
  timeBucket: TTimeBucket;
  type: TTSType;
}

export interface IColumnInfoReferencedColumn {
  __typename: TReferencedColumnTypename;
  displayName: string;
  guid: string;
}

export interface IFilter {
  __typename: string;
  filterContent: IFilterContent[];
  filterId: string;
}

export interface IFilterContent {
  __typename: string;
  filterType: string;
  negate: boolean;
  value: ITSValue[];
}

export interface ITSValue {
  __typename: string;
  key: string;
}

export interface IGroupId {
  __typename: string;
  answerColumnId: string;
  dataSourceId: null;
  logicalColumnId: null;
}

export interface IHeadlineVisibilityMap {
  __typename: string;
  columnId: string;
  isVisible: boolean;
}

interface Permission {
  __typename: string;
  dataSourceAccessLevel: string;
  dataSourceNamesWithNoAccess: unknown[];
  objectAccessLevel: string;
}

interface ReportBookMetadata {
  headerMetadata: HeaderMetadata;
}

export interface HeaderMetadata {
  id: string;
  name: string;
  description: string;
  isNewAnswer: boolean;
  isHidden: boolean;
  loading: boolean;
}

export interface User {
  userName: string;
  userGUID: string;
  userEmail: string;
}

export interface Visualization {
  __typename: string;
  clientState: IClientState;
  columns: VisualizationColumn[];
  config: Config;
  id: string;
  sortInfo: unknown[];
  sortOrder: unknown[];
  suggestedConfig: SuggestedConfig[];
  topInfo: unknown[];
  vizProp: VizProp;
}

export interface VisualizationColumn {
  __typename: string;
  column: IXElement;
  legacyMetricDefinition: null;
}

export interface Config {
  __typename: ConfigTypename;
  axisConfig: ConfigAxisConfig[];
  chartType: string;
  isLocked: boolean;
}

export type ConfigTypename = "ChartConfig";

export interface ConfigAxisConfig {
  __typename: AxisConfigTypename;
  category: unknown[];
  color: unknown[];
  size: null;
  sort: unknown[];
  x: IXElement[];
  y: IXElement[];
}

export type AxisConfigTypename = "AxisConfig";

export interface SuggestedConfig {
  __typename: ConfigTypename;
  axisConfig: SuggestedConfigAxisConfig[];
  chartType: string;
  isLocked: boolean;
}

export interface SuggestedConfigAxisConfig {
  __typename: AxisConfigTypename;
  category: IXElement[];
  color: IXElement[];
  size: IXElement | null;
  sort: unknown[];
  x: IXElement[];
  y: IXElement[];
}

export interface VizProp {
  __typename: string;
  axisProperties: AxisProperty[];
  chartProperties: ChartProperties;
  columnProperties: ColumnPropertyElement[];
  customColorSelectorArray: unknown[];
  multiColorSeriesColors: unknown[];
  seriesColors: SeriesColor[];
  systemMultiColorSeriesColors: unknown[];
  systemSeriesColors: SystemSeriesColor[];
  version: string;
}

export interface AxisProperty {
  __typename: string;
  id: string;
  properties: Properties;
}

export interface Properties {
  __typename: string;
  axisType: string;
  format: null;
  isOpposite: boolean | null;
  linkedColumns: string[];
  name: null;
  yAxisRange: null;
}

export interface ChartProperties {
  __typename: string;
  allLabels: boolean;
  axisExtremes: null;
  chartSpecific: ChartSpecific;
  dataSize: null;
  gridLines: null;
  isZoomed: null;
  mapviewport: null;
  responsiveLayoutDisabled: null;
  responsiveLayoutPreference: null;
  showLegend: null;
  showLinearRegressionLine: null;
  showStackedLabels: boolean;
  visibleSeriesNames: unknown[];
}

export interface ChartSpecific {
  __typename: string;
  customProps: null;
  dataFieldArea: null;
  hidePivotSummaries: null;
  isHeatmapOverlayed: boolean;
  isStackedAsPercent: null;
  markersEnabled: null;
  pivotState: PivotState;
  stackedAsPercentFormat: null;
  summaryFormat: null;
  summaryMode: null;
  useFlatLayout: null;
}

export interface PivotState {
  __typename: string;
  columnExpandedPaths: unknown[];
  fields: unknown[];
  rowExpandedPaths: unknown[];
}

export interface ColumnPropertyElement {
  __typename: string;
  columnId: string;
  columnProperty: ColumnPropertyColumnProperty;
}

export interface ColumnPropertyColumnProperty {
  __typename: string;
  conditionalFormatting: null;
  dataLabels: boolean;
}

export interface SeriesColor {
  __typename: string;
  color: string;
  serieName: string;
}

export interface SystemSeriesColor {
  __typename?: string;
  color: string;
  serieName: string;
}

export type TTSActionPayload = MessagePayload & {
  data: ICustomAction;
  status?: string;
  type: "customAction";
};

export type TTSAnswerFormula = {
  expr: string;
};

export type TTSAnswerTML = {
  answer: {
    formulas: TTSAnswerFormula[];
  };
};
