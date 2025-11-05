export interface IEdoc {
  guid: string;
  liveboard: ILiveboard;
}

export interface ITMLInfo {
  filename: string;
  name: string;
  id: string;
  type: string;
  status: {
    status_code: string;
  };
}

export interface ILiveboard {
  name: string;
  description: string;
  visualizations: IVisualization[];
  filters: Filter[];
  layout: Layout;
}

interface Filter {
  column: string[];
  oper: string;
  values: string[];
  is_mandatory: boolean;
}

interface Layout {
  tabs: Tab[];
}

interface Tab {
  name: string;
  description: string;
  tiles: Tile[];
}

interface Tile {
  visualization_id: string;
  x: number;
  y: number;
  height: number;
  width: number;
}

export interface IVisualization {
  id: string;
  answer: IAnswer;
  viz_guid: string;
}

interface IAnswer {
  name: string;
  description: string;
  tables: TableElement[];
  search_query: string;
  answer_columns: AnswerColumn[];
  table: PurpleTable;
  chart: Chart;
  display_mode: DisplayMode;
}

interface AnswerColumn {
  name: string;
  format?: Format;
  custom_name?: string;
}

interface Format {
  category: string;
  numberFormatConfig: NumberFormatConfig;
  isCategoryEditable: boolean;
}

interface NumberFormatConfig {
  unit: string;
  decimals: number;
  negativeValueFormat: string;
  toSeparateThousands: boolean;
}

interface Chart {
  type: string;
  chart_columns: ChartColumn[];
  axis_configs: AxisConfig[];
  client_state: string;
  client_state_v2: string;
}

interface AxisConfig {
  y: Y[];
  x?: string[];
  color?: string[];
}

type Y = string;

interface ChartColumn {
  column_id: string;
}

type DisplayMode = "CHART_MODE";

interface PurpleTable {
  table_columns: TableColumn[];
  ordered_column_ids: string[];
  client_state: string;
  client_state_v2: string;
}

interface TableColumn {
  column_id: string;
  show_headline: boolean;
}

interface TableElement {
  id: string;
  name: string;
  fqn: string;
}
