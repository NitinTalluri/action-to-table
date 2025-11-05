// ******** DATE RANGE FILTER UTILS ******** //

export const isValidDateString = (dateStr: unknown): dateStr is string => {
  if (!dateStr) return false;
  if (typeof dateStr !== "string") return false;
  const isCorrectFormat = RegExp(/^\d{4}-\d{2}-\d{2}$/).test(dateStr);
  return isCorrectFormat;
};

export const getDateFilterVal = (
  val: unknown,
): [string | undefined, string | undefined] => {
  if (!Array.isArray(val)) return [undefined, undefined];
  if (val.length !== 2) return [undefined, undefined];
  if (!val.every((v) => typeof v === "string")) return [undefined, undefined];
  return [val[0], val[1]];
};

export const formatDateToYYYYMMDD = (date: Date): string => {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0"); // Months are zero-based
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
};

export const getLowerDate = (
  dateStr1?: string | null,
  dateStr2?: string | null,
): string => {
  if (!dateStr1 && !dateStr2) return "";
  if (!dateStr1) return dateStr2 || "";
  if (!dateStr2) return dateStr1 || "";
  const date1 = new Date(dateStr1);
  const date2 = new Date(dateStr2);

  return date1 < date2 ? dateStr1 : dateStr2;
};

export const getLargerDate = (
  dateStr1?: string | null,
  dateStr2?: string | null,
): string => {
  if (!dateStr1 && !dateStr2) return "";
  if (!dateStr1) return dateStr2 || "";
  if (!dateStr2) return dateStr1 || "";
  const date1 = new Date(dateStr1);
  const date2 = new Date(dateStr2);

  return date1 > date2 ? dateStr1 : dateStr2;
};
