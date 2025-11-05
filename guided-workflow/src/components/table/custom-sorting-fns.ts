import { Row } from "@tanstack/react-table";
import { z } from "zod";

const arraySchema = z.array(z.union([z.string(), z.number()]));

export const simpleArraySort = <T>(
  a: Row<T>,
  b: Row<T>,
  key: keyof Row<T>["original"],
) => {
  const arrayA = arraySchema.safeParse(a.original[key] || []);
  const arrayB = arraySchema.safeParse(b.original[key] || []);
  if (!arrayA.success || !arrayB.success) return 0;
  for (let i = 0; i < Math.min(arrayA.data.length, arrayB.data.length); i++) {
    const valAAsType = isNaN(Number(arrayA.data[i]))
      ? String(arrayA.data[i]).toLowerCase()
      : Number(arrayA.data[i]);
    const valBAsType = isNaN(Number(arrayB.data[i]))
      ? String(arrayB.data[i]).toLowerCase()
      : Number(arrayB.data[i]);
    if (valAAsType < valBAsType) return -1;
    if (valAAsType > valBAsType) return 1;
  }
  return arrayA.data.length - arrayB.data.length;
};

export const objectArraySort = <T>(
  a: Row<T>,
  b: Row<T>,
  key: keyof Row<T>["original"],
  getObjectMap: (rowValue: T[keyof T]) => (string | number)[],
) => {
  const arrayA = getObjectMap(a.original[key]);
  const arrayB = getObjectMap(b.original[key]);
  for (let i = 0; i < Math.min(arrayA.length, arrayB.length); i++) {
    const valAAsType = isNaN(Number(arrayA[i]))
      ? String(arrayA[i]).toLowerCase()
      : Number(arrayA[i]);
    const valBAsType = isNaN(Number(arrayB[i]))
      ? String(arrayB[i]).toLowerCase()
      : Number(arrayB[i]);
    if (valAAsType < valBAsType) return -1;
    if (valAAsType > valBAsType) return 1;
  }
  return arrayA.length - arrayB.length;
};
