import { Row } from "@tanstack/react-table";

export const dateBetweenFilterFn = (
  row: Row<unknown>,
  columnId: string,
  value: unknown,
) => {
  const val = row.getValue(columnId);
  if (typeof val !== "string") return false;
  const date = new Date(val);
  if (!(date instanceof Date)) {
    console.warn(
      `Value of column "${columnId}" is expected to be a date, but got ${date}`,
    );
    return false;
  }
  if (!Array.isArray(value)) {
    console.warn(
      `Filter value of column "${columnId}" is expected to be an array of two dates, but got ${value}`,
    );
    return false;
  }
  const [startString, endString] = value ?? []; // value => two date input values
  if (typeof startString !== "string" || typeof endString !== "string") {
    return false;
  }
  // ensure dates are valid Date objects
  // add time to start and end dates strings if not already present
  const startTime = "T00:00:00.000Z"; // time is set to midnight
  const endTime = "T23:59:59.999Z"; // time is set to end of day
  const start =
    startString && startString.includes("T")
      ? new Date(startString)
      : new Date(startString + startTime);
  const end =
    endString && endString.includes("T")
      ? new Date(endString)
      : new Date(endString + endTime);
  if (!(start instanceof Date) || !(end instanceof Date)) {
    console.warn(
      `Filter value of column "${columnId}" is expected to be an array of two dates, but got ${value}`,
    );
    return false;
  }

  // If one filter defined and date is undefined, filter it
  if ((start || end) && !date) {
    return false;
  }
  if (start && !end) {
    return date.getTime() >= start.getTime();
  } else if (!start && end) {
    return date.getTime() <= end.getTime();
  } else if (start && end) {
    return date.getTime() >= start.getTime() && date.getTime() <= end.getTime();
  }

  return true;
};

export const multiSelectFilterFn = <T extends object>(
  row: Row<T>,
  columnId: string,
  value: unknown,
) => {
  if (!value) return true;
  if (!Array.isArray(value)) return true;
  if (!value.length) return true;
  return value.some((val) => {
    if (columnId in row.original) {
      // value comes in as strings, so we need to convert to number or boolean if possible
      const valAsBoolean =
        val === "true" || val === "false" ? val === "true" : val;
      const valAsType = isNaN(Number(val)) ? valAsBoolean : Number(val);
      return row.original[columnId as keyof typeof row.original] === valAsType;
    }
    return false;
  });
};

export const multiSelectObjectFilterFn = <T extends object>(
  row: Row<T>,
  columnId: string,
  value: unknown,
  objectFilter: (rowValue: T[keyof T], query: unknown) => boolean,
) => {
  if (!value) return true;
  if (!Array.isArray(value)) return true;
  if (!value.length) return true;
  return value.some((val) => {
    if (!(columnId in row.original)) {
      return false;
    }
    return objectFilter(
      row.original[columnId as keyof typeof row.original],
      val,
    );
  });
};
