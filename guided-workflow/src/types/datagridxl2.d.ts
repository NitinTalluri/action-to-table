declare module "@datagridxl/datagridxl2" {
  type TLabel = {
    numbers: string;
    letters: string;
  };

  type TColRef = {
    align: "left" | "center" | "right";
    field: string;
    id: number;
    level: number;
    parent_id?: number;
    title: string;
    width: number;
  };

  type TRowRef = {
    id: number;
    title?: string;
  };

  export type TColHeaderLabelFunc = (
    index: number,
    coord: number,
    colRef: TColRef,
    labels: TLabel,
  ) => string;

  export type TRowHeaderLabelFunc = (
    index: number,
    coord: number,
    rowRef: TRowRef,
    labels: TLabel,
  ) => string;

  type TColObj = {
    title?: string;
    field?: string;
    align?: "left" | "center" | "right";
    width?: number;
    source?: string | number;
    _hide?: boolean;
  };

  export type ConvertedDataType = string | undefined | null;
  export type T2DArray = ConvertedDataType[][];
  export type T2ObjArray = Record<string, ConvertedDataType>[];
  type TCellSelection = { x: number; y: number };
  type TRangeSelection = [TCellSelection, TCellSelection][];
  type TSelection = TCellSelection | TRangeSelection;
  type TSelectObject = { range: TCellSelection[]; type: "cell" };
  export type DGInputData<T = unknown> = T extends T2DArray
    ? T
    : T extends T2ObjArray
      ? T
      : unknown;

  export interface DataGridXLOptions<Data extends DGInputData<Data> = unknown> {
    /**
     * https://v2.datagridxl.com/api/options
     */

    allowEditCells?: boolean; // default: true
    allowFillCells?: boolean; // default: true
    fillCellsDirection?: "x" | "y" | "xy"; // default: "xy"
    allowDeleteCols?: boolean; // default: true
    allowFreezeCols?: boolean; // default: true
    allowHideCols?: boolean; // default: true
    allowInsertCols?: boolean; // default: true
    allowMoveCols?: boolean; // default: true
    allowResizeCols?: boolean; // default: true
    allowDeleteRows?: boolean; // default: true
    allowFreezeRows?: boolean; // default: true
    allowHideRows?: boolean; // default: true
    allowInsertRows?: boolean; // default: true
    allowMoveRows?: boolean; // default: true
    allowSort?: boolean; // default: true
    instanceActivate?: boolean; // default: false
    colAlign?: "left" | "center" | "right"; // default: "left"
    colHeaderHeight?: number; // default: 28
    colHeaderLabelAlign?: "left" | "center" | "right"; // default: "left"
    colHeaderLabelFunc?: TColHeaderLabelFunc; // default: undefined
    colHeaderLabelPrefix?: string; // default: ""
    colHeaderLabelSuffix?: string; // default: ""
    colHeaderLabelType?: "letters" | "numbers"; // default: "letters"
    columns?: TColObj[];
    colWidth?: number; // default: 100
    frozenCols?: number; // default: 0
    frozenRows?: number; // default: 0
    rowHeaderLabelAlign?: "left" | "center" | "right"; // default: "center"
    rowHeaderLabelFunction?: TRowHeaderLabelFunc; // default: undefined
    rowHeaderLabelPrefix?: string; // default: ""
    rowHeaderLabelSuffix?: string; // default: ""
    rowHeaderLabelType?: "letters" | "numbers"; // default: "numbers"
    rowHeaderWidth?: number; // default: +5
    rowHeight?: number; // default: 28
    allowCopy?: boolean; // default: true
    allowCut?: boolean; // default: true
    allowPaste?: boolean; // default: true
    expandSheetOnPaste?: boolean; // default: true
    instanceCut?: boolean; // default: false
    data?: Data; // default: 3x3 empty array
    fontFamily?: string; // default: "sans-serif"
    fontSize?: number; // default: 13
  }

  type TPrefixEvent<
    Prefix extends string,
    Event extends string,
  > = `${Prefix}${Event}`;
  type TBeforeEvent<Event> = TPrefixEvent<"before", Event>;

  type TChangeEvent = "change";
  type TReadyEvent = "ready";
  type TDeleteColsEvent = "deletecols";
  type TBeforeDeleteColsEvent = TBeforeEvent<TDeleteColsEvent>;
  type TFreezeColsEvent = "freezecols";
  type TBeforeFreezeColsEvent = TBeforeEvent<TFreezeColsEvent>;
  type THideColsEvent = "hidecols";
  type TBeforeHideColsEvent = TBeforeEvent<THideColsEvent>;
  type TInsertColsEvent = "insertcols";
  type TBeforeInsertColsEvent = TBeforeEvent<TInsertColsEvent>;
  type TMoveColsEvent = "movecols";
  type TBeforeMoveColsEvent = TBeforeEvent<TMoveColsEvent>;
  type TResizeColsEvent = "resizecols";
  type TBeforeResizeColsEvent = TBeforeEvent<TResizeColsEvent>;
  type TShowColsEvent = "showcols";
  type TBeforeShowColsEvent = TBeforeEvent<TShowColsEvent>;
  type THideRowsEvent = "hiderows";
  type TBeforeHideRowsEvent = TBeforeEvent<THideRowsEvent>;
  type TInsertRowsEvent = "insertrows";
  type TBeforeInsertRowsEvent = TBeforeEvent<TInsertRowsEvent>;
  type TMoveRowsEvent = "moverows";
  type TBeforeMoveRowsEvent = TBeforeEvent<TMoveRowsEvent>;
  type TShowRowsEvent = "showrows";
  type TBeforeShowRowsEvent = TBeforeEvent<TShowRowsEvent>;
  type TCopyEvent = "copy";
  type TBeforeCopyEvent = TBeforeEvent<TCopyEvent>;
  type TCutEvent = "cut";
  type TBeforeCutEvent = TBeforeEvent<TCutEvent>;
  type TPasteEvent = "paste";
  type TBeforePasteEvent = TBeforeEvent<TPasteEvent>;
  type TResizeEvent = "resize";
  type TSetSelectionEvent = "setselection";
  type TRedoEvent = "redo";
  type TBeforeRedoEvent = TBeforeEvent<TRedoEvent>;
  type TUndoEvent = "undo";
  type TBeforeUndoEvent = TBeforeEvent<TUndoEvent>;
  type TSetViewportEvent = "setviewportposition";
  type TSetCellValuesEvent = "setcellvalues";
  type TBeforeSetCellValuesEvent = TBeforeEvent<TSetCellValuesEvent>;

  type TActivate = "activate";
  type TDeactivate = "deactivate";

  type TEvent =
    | TChangeEvent
    | TReadyEvent
    | TDeleteColsEvent
    | TBeforeDeleteColsEvent
    | TFreezeColsEvent
    | TBeforeFreezeColsEvent
    | THideColsEvent
    | TBeforeHideColsEvent
    | TInsertColsEvent
    | TBeforeInsertColsEvent
    | TMoveColsEvent
    | TBeforeMoveColsEvent
    | TResizeColsEvent
    | TBeforeResizeColsEvent
    | TShowColsEvent
    | TBeforeShowColsEvent
    | THideRowsEvent
    | TBeforeHideRowsEvent
    | TInsertRowsEvent
    | TBeforeInsertRowsEvent
    | TMoveRowsEvent
    | TBeforeMoveRowsEvent
    | TShowRowsEvent
    | TBeforeShowRowsEvent
    | TCopyEvent
    | TBeforeCopyEvent
    | TCutEvent
    | TBeforeCutEvent
    | TPasteEvent
    | TBeforePasteEvent
    | TResizeEvent
    | TSetSelectionEvent
    | TRedoEvent
    | TBeforeRedoEvent
    | TUndoEvent
    | TBeforeUndoEvent
    | TSetViewportEvent
    | TActivate
    | TDeactivate
    | TSetCellValuesEvent
    | TBeforeSetCellValuesEvent;

  type TClipboardSelectionEvent =
    | TCopyEvent
    | TBeforeCopyEvent
    | TCutEvent
    | TBeforeCutEvent;

  type TClipboardEventPayload = {
    text: string; // tab separated values
    cellRange: TRangeSelection;
  };

  type TPasteEventPayload = {
    text: string; // tab separated values
  };

  type TChangeEventPayload = {
    colIds: number[];
    rowIds: number[];
    values: string[];
    selection: TSelectObject[];
  };

  type TCancelReturn = false | void;

  class DataGridEvents {
    on(
      event: TClipboardSelectionEvent,
      handler: (payload: TClipboardEventPayload) => TCancelReturn,
    );
    on(
      event: TPasteEvent | TBeforePasteEvent,
      handler: (payload: TPasteEventPayload) => TCancelReturn,
    );
    on(
      event: TSetCellValuesEvent | TBeforeSetCellValuesEvent,
      handler: (payload: {
        colIds: number[];
        rowIds: number[];
        values: string[];
        selection: TSelectObject[];
      }) => TCancelReturn,
    );
    on(event: TEvent, handler: (...args: unknown[]) => TCancelReturn);
    on(
      event: TChangeEvent,
      handler: (payload: TChangeEventPayload) => TCancelReturn,
    );

    off(event: TEvent, handler: (...args: unknown[]) => TCancelReturn);

    off(
      event: TSetCellValuesEvent | TBeforeSetCellValuesEvent,
      handler: (payload: {
        colIds: number[];
        rowIds: number[];
        values: string[];
        selection: TSelectObject[];
      }) => TCancelReturn,
    );
    off(event: TChangeEvent, handler: (payload: TChangeEventPayload) => void);
  }

  export default class DataGridXL<Data extends DGInputData<Data> = unknown> {
    constructor(element: HTMLElement, options: DataGridXLOptions<Data>);

    public events: DataGridEvents;

    clearCellValues(cells: TSelection);

    getData(): Data;

    deleteRows(rows: number | [number, number]);

    deleteCols: ((col: number) => void) | ((col: [number]) => void);

    static createEmptyData(nRows: number, nCols: number): null[][];

    setViewportPosition(position: TCellSelection);

    setCellSelection(selection: TSelection);
    setRowSelection(selection: TCellSelection);

    getCellSelection(): TSelection;

    destroy();

    moveCellCursorToSheetEnd(): void;
    insertEmptyRows(nRows: number);
    setCellValues(selection: TCellSelection, values: string[]): void;
    setCellValues(selection: TRangeSelection, values: string[][]): void;
    search(needle: string): void;
    clearSearch(): void;
  }
}
