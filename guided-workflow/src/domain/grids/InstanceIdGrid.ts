import { z } from "zod";

export const InstanceIdGridSchema = z.object({
  instance_id: z.coerce
    .string()
    .transform((val) => val.trim())
    .refine((str) => /^\d+$/.test(str), {
      message: "Only numeric strings are allowed",
    })
    .transform((s) => parseInt(s)),
});
export type TInstanceId = z.infer<typeof InstanceIdGridSchema>;
export const InstanceIdGridArraySchema = z
  .array(InstanceIdGridSchema)
  .superRefine((val, ctx) => {
    const idsSeen = new Set<TInstanceId["instance_id"]>();
    let row = 0;
    for (const instance of val) {
      if (idsSeen.has(instance.instance_id)) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          path: [row, "instance_id"],
          message: `Duplicate Id: ${instance.instance_id}`,
        });
      }
      idsSeen.add(instance.instance_id);
      row++;
    }
  });
