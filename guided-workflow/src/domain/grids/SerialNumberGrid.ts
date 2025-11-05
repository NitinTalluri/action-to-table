import { z } from "zod";

const RemoveControlRegex = /\p{C}/gu;
export const SerialNumberGridSchema = z.object({
  serial_number: z.coerce
    .string()
    .transform((val) => val.replace(RemoveControlRegex, "").trim()),
});

export type TSerialNumberGrid = z.infer<typeof SerialNumberGridSchema>;
export const SerialNumberGridArraySchema = z
  .array(SerialNumberGridSchema)
  .superRefine((val, ctx) => {
    const idsSeen = new Set<TSerialNumberGrid["serial_number"]>();
    let row = 0;
    for (const serial of val) {
      if (idsSeen.has(serial.serial_number)) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          path: [row, "serial_number"],
          message: `Duplicate serial number: ${serial.serial_number}`,
        });
      }
      idsSeen.add(serial.serial_number);
      row++;
    }
  });
