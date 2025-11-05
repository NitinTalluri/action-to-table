import "../scss/components/_datatable.scss";

import CancelIcon from "@mui/icons-material/Cancel";
import DeleteIcon from "@mui/icons-material/Delete";
import EditIcon from "@mui/icons-material/Edit";
import SaveIcon from "@mui/icons-material/Save";
import ShareIcon from "@mui/icons-material/Share";
import IconButton from "@mui/material/IconButton";
import Typography from "@mui/material/Typography";
import { useState } from "react";
import { Column, useTable } from "react-table";

import EngagementShare from "../features/engagements/EngagementShare";

export type TEditableColumn<D extends object> = Column<D> & {
  canEdit?: boolean;
};

export type TRowWithEngagement = {
  engagement_name: string;
  dc_engagement_id: number;
};

type TDataTableProps<D extends object> = {
  columns: TEditableColumn<D>[];
  data: D[];
  onSave: ((d: D) => void) | null;
  onDelete: ((d: D) => void) | null;
  onRowClick?: ((d: D) => void) | null;
  isEditable?: boolean;
};

const DataTable = <D extends object = object>(props: TDataTableProps<D>) => {
  const {
    columns,
    data,
    onSave: onSaveParam,
    onDelete,
    onRowClick: onRowClickParam,
    isEditable: isEditableParam,
  } = props;
  const onSave = onSaveParam ?? null;
  const onRowClick = onRowClickParam ?? null;
  const isEditable = isEditableParam ?? null;
  const [editingRowId, setEditingRowId] = useState<string | null>(null);
  const [editingRowData, setEditingRowData] = useState<D | null>(null);
  const [open, setOpen] = useState(false);
  const [selectedEngagementId, setSelectedEngagementId] = useState<
    number | null
  >(null);

  const { getTableProps, getTableBodyProps, headerGroups, rows, prepareRow } =
    useTable<D>({ columns, data });

  if (data.length === 0) {
    return (
      <Typography
        variant="body1"
        color="textSecondary"
        align="center"
        style={{ marginTop: "30px" }}
      >
        No data available
      </Typography>
    );
  }

  const handleEditClick = (rowId: string, rowOriginalData: D) => {
    setEditingRowId(rowId);
    setEditingRowData(rowOriginalData);
  };

  const handleSaveClick = () => {
    setEditingRowId(null);
    if (onSave && editingRowData) {
      onSave(editingRowData);
    }
  };

  const handleCancelClick = () => {
    setEditingRowId(null);
    setEditingRowData(null);
  };

  const handleDeleteClick = (rowId: string, rowOriginalData: D) => {
    if (onDelete) {
      onDelete(rowOriginalData);
    }
  };

  const handleChange = (name: string, value: string) => {
    setEditingRowData(
      (prev) =>
        ({
          ...prev,
          [name]: value,
        }) as D,
    );
  };

  const handleClose = () => {
    setOpen(false);
    setSelectedEngagementId(null);
  };

  return (
    <div className="data-table-wrapper ">
      <table
        className="data-table"
        {...getTableProps()}
        style={{ textAlign: "left" }}
      >
        <thead>
          {headerGroups.map((headerGroup) => {
            const { key, ...headerGroupProps } =
              headerGroup.getHeaderGroupProps();

            return (
              <tr key={key} {...headerGroupProps}>
                {headerGroup.headers.map((column) => {
                  const { key, ...columnHeaderProps } = column.getHeaderProps();

                  return (
                    <th key={key} {...columnHeaderProps}>
                      {column.render("Header")}
                    </th>
                  );
                })}
                <th>Actions</th>
              </tr>
            );
          })}
        </thead>
        <colgroup>
          {columns.map((c, i: number) => {
            const k = c.Header ? c.Header.toString() : `${i}`;
            return <col key={k} />;
          })}
        </colgroup>
        <tbody {...getTableBodyProps()}>
          {rows.map((row) => {
            prepareRow(row);
            const isRowEditable = editingRowId === row.id;
            const { key, ...rowProps } = row.getRowProps();

            return (
              <tr
                key={key}
                {...rowProps}
                onClick={() => onRowClick && onRowClick(row.original)}
              >
                {row.cells.map((cell) => {
                  const cellValue = cell.value;
                  const cellId = cell.column.id;

                  const { key, ...cellProps } = cell.getCellProps();

                  return (
                    <td key={key} {...cellProps}>
                      {isRowEditable &&
                      (cell.column as TEditableColumn<D>).canEdit !== false ? (
                        <input
                          defaultValue={cellValue}
                          className="responsive-input"
                          onClick={(e) => e.stopPropagation()}
                          onChange={(e) => handleChange(cellId, e.target.value)}
                        />
                      ) : (
                        cell.render("Cell")
                      )}
                    </td>
                  );
                })}

                <td
                  style={{
                    position: `${isRowEditable ? "sticky" : "initial"}`,
                    right: `${isRowEditable ? "0" : "initial"}`,
                    background: `${isRowEditable ? "white" : "initial"}`,
                  }}
                >
                  <div style={{ display: "flex" }}>
                    {isRowEditable && isEditable ? (
                      <>
                        <IconButton
                          onClick={(event) => {
                            event.stopPropagation();
                            handleSaveClick();
                          }}
                        >
                          <SaveIcon />
                        </IconButton>
                        <IconButton
                          onClick={(event) => {
                            event.stopPropagation();
                            handleCancelClick();
                          }}
                        >
                          <CancelIcon />
                        </IconButton>
                      </>
                    ) : (
                      <>
                        {isEditable && (
                          <IconButton
                            onClick={(event) => {
                              event.stopPropagation();
                              handleEditClick(row.id, row.original);
                            }}
                          >
                            <EditIcon />
                          </IconButton>
                        )}
                        <IconButton
                          onClick={(event) => {
                            event.stopPropagation();
                            handleDeleteClick(row.id, row.original);
                          }}
                        >
                          <DeleteIcon />
                        </IconButton>

                        {(row.original as D & TRowWithEngagement)
                          .engagement_name && (
                          <IconButton
                            onClick={() => {
                              setSelectedEngagementId(
                                (row.original as D & TRowWithEngagement)
                                  .dc_engagement_id,
                              );
                              setOpen(true);
                            }}
                          >
                            <ShareIcon />
                          </IconButton>
                        )}
                      </>
                    )}
                  </div>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
      {selectedEngagementId && (
        <EngagementShare
          engagement={selectedEngagementId}
          open={open}
          handleClose={handleClose}
        />
      )}
    </div>
  );
};

export default DataTable;
