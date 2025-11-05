import { DateTime } from "luxon";
import { z } from "zod";

import { DateFormatEnum, TDateFormatEnum } from "~/domain/grids/Cell";

export const parseDateString = (dateString: string): string => {
  const dt = new Date(dateString);
  return dt.toLocaleDateString();
};

type TParsedDateTimeString = {
  date: string;
  time: string;
};

export const parseDateTimeString = (
  dateString: string,
): TParsedDateTimeString => {
  const dt = new Date(dateString);
  const date = dt.toLocaleDateString();
  const time = dt.toLocaleTimeString();
  return { date, time };
};

export const getDeltaDate = (days: number): Date => {
  const date = new Date();
  date.setDate(date.getDate() + days);
  date.setHours(0, 0, 0, 0);
  return date;
};

export const formatDate = (d: Date) => {
  return d.toLocaleString("en-US", {
    month: "2-digit",
    day: "2-digit",
    year: "numeric",
  });
};

export const formatIsoDate = (d: Date) => {
  /**
    YYYY-MM-DD format to work with native date input
   */
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
};

export const formatDateIntl = (dateString: number | string | Date) => {
  const options: Intl.DateTimeFormatOptions = {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  };
  return new Date(dateString).toLocaleDateString(undefined, options);
};

export const isDayFirstLocale = () => {
  const formatter = new Intl.DateTimeFormat(navigator.language || "en-US");
  const testDate = new Date(Date.UTC(2000, 1, 16)); // year, month, day
  const parts = formatter.formatToParts(testDate);
  return parts[0].type === "day";
};

const isValidDate = (date: Date) =>
  date instanceof Date && !isNaN(date.valueOf());

// returns date as ISO (date only) string based on the navigator lang...
// ...or the user's browser's navigator lang if param is not provided
export const getFormattedISODate = (
  dateStr?: string | null,
  isDayFirst?: boolean,
  fallbackDateStr = "",
): string => {
  // if no date, return fallback
  if (!dateStr) {
    return fallbackDateStr;
  }
  // wrapped in try catch incase dateStr is the wrong format
  try {
    let joinedDateStr = "";
    // split into positions, there should be three (day, month, year)...
    // ...but order is unknown without lang assumptions
    const [first, second, third] = dateStr.split(/[-/]/);
    const dayFirst =
      typeof isDayFirst === "boolean" ? isDayFirst : isDayFirstLocale();
    // we can build out this switch as we support more languages
    if (dayFirst) {
      joinedDateStr = `${third}-${second}-${first}`;
    } else {
      joinedDateStr = `${third}-${first}-${second}`;
    }
    return isValidDate(new Date(joinedDateStr))
      ? joinedDateStr
      : fallbackDateStr;
  } catch {
    return fallbackDateStr;
  }
};

// get number of days between today and a date
export const getDayDiff = (dueDate: string) => {
  const today = new Date().getTime();
  const date = new Date(dueDate).getTime();
  const diff = date - today;

  const millisecondsPerDay = 1000 * 60 * 60 * 24;
  const diffInDays = Math.round(diff / millisecondsPerDay);

  return diffInDays;
};

/**
 * Extracts the ISO week number from a date.
 *
 * @param date
 *
 * The ISO definition of week number is:
 * - Week 1 is the week with the first Thursday of the year.
 * - Weeks start on Monday, and end on Sunday.
 * - Week numbers are between 1 and 53
 * - 53 weeks only occur if, January 1st is a Thursday OR December 31st is a Thursday
 */

export const getISOWeekNumber = (date: Date) => {
  const target = new Date(date.valueOf());

  // Set to nearest Thursday: current date + 4 - current day number
  // Make Sunday's day number 7 instead of 0 (ISO uses 1-7)
  const dayNumber = (target.getDay() + 6) % 7;
  target.setDate(target.getDate() - dayNumber + 3);

  // Get first Thursday of the year
  const firstThursday = new Date(target.getFullYear(), 0, 4);
  const firstDayNumber = (firstThursday.getDay() + 6) % 7;
  firstThursday.setDate(firstThursday.getDate() - firstDayNumber + 3);

  // Calculate week number
  return (
    1 +
    Math.round(
      (target.getTime() - firstThursday.getTime()) / (7 * 24 * 60 * 60 * 1000),
    )
  );
};

export const generateDateValidationSchema = (
  dateCols: string[],
  dateFormat?: TDateFormatEnum,
) => {
  const formats = dateFormat ? [dateFormat] : DateFormatEnum.options;

  const validationSchema = z.array(
    z.object(
      dateCols.reduce<Record<string, z.ZodTypeAny>>((acc, key) => {
        acc[key] = z
          .string()
          .nullish()
          .refine(
            (value) =>
              !value ||
              formats.some(
                (format) => DateTime.fromFormat(value, format).isValid,
              ),
            {
              message: `Value must be of valid formats: ${formats.join(", ")}`,
            },
          );
        return acc;
      }, {}),
    ),
  );

  return validationSchema;
};
