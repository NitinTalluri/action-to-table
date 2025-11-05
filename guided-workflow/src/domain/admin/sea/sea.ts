import { z } from "zod";

const CellString = z.coerce
  .string()
  .nullish()
  .catch(null)
  .transform((val) => {
    if (typeof val === "string") {
      return val.trim();
    }
    return val;
  })
  .transform((val) => {
    if (val === "" || val === null || val === undefined) {
      return null;
    }
    return val;
  });

export const SEADataSchema = z.object({
  fmw_flag: CellString,
  web_order_id: CellString,
  bp_name: CellString,
  sales_level_1: CellString,
  sales_level_2: CellString,
  sales_level_3: CellString,
  end_customer_global_ultimate_name: CellString,
  end_customer_global_ultimate_id: CellString,
  ca_service_bookings_net: CellString,
  annual_bookings_net: CellString,
  subscription_reference_id: CellString,
  date_booked: CellString,
});

export type TSEAData = z.infer<typeof SEADataSchema>;
type TSEADataInput = z.input<typeof SEADataSchema>;
type TSEADataOutput = z.output<typeof SEADataSchema>;

export const SEADataArraySchema: z.ZodType<
  TSEADataOutput[],
  z.ZodTypeDef,
  TSEADataInput[]
> = z.array(SEADataSchema);
