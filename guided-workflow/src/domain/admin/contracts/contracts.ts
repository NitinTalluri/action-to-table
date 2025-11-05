import { z } from "zod";

const DateFormatRegex = /^\d{1,2}\/\d{1,2}\/\d{4}$/;
const CurrencyFormatRegex = /\$/;

const testDate = (value: string) =>
  DateFormatRegex.test(value) && !isNaN(Date.parse(value));

const currency: z.ZodType<number, z.ZodTypeDef, string> = z.coerce
  .string({
    required_error: "Currency is required",
  })
  .transform((val) => val.replace(CurrencyFormatRegex, "").trim())
  .transform((val) => parseInt(val.replace(/,/g, "")));

const ContractBaseSchema = z.object({
  booking_contract: z.coerce
    .number({
      invalid_type_error: "Booking Contract must be a number",
      required_error: "Booking Contract is required",
    })
    .positive({
      message: "Booking Contract must be a positive number",
    }),
  account_name: z.string({
    required_error: "Account Name is required",
    invalid_type_error: "Account Name must be text",
  }),
  booked_sav_1: z.string({
    required_error: "Booked SAV 1 is required",
    invalid_type_error: "Booked SAV 1 must be text",
  }),
  booked_sav_2: z.string({
    required_error: "Booked SAV 2 is required",
    invalid_type_error: "Booked SAV 2 must be text",
  }),
  booked_sav_3: z.string({
    required_error: "Booked SAV 3 is required",
    invalid_type_error: "Booked SAV 3 must be text",
  }),
  booked_theater: z.string({
    required_error: "Booked Theater is required",
    invalid_type_error: "Booked Theater must be text",
  }),
  sold_as_service_type: z.string({
    required_error: "Sold As Service Type is required",
    invalid_type_error: "Sold As Service Type must be text",
  }),
  sold_as_pricing_type: z.string({
    required_error: "Sold As Pricing Type is required",
    invalid_type_error: "Sold As Pricing Type must be text",
  }),
  buying_program_type: z.string({
    required_error: "Buying Program Type is required",
    invalid_type_error: "Buying Program Type must be text",
  }),
  ib_calc_sw_allocation: z.coerce.number({
    invalid_type_error: "IB Calc SW Allocation must be a number",
    required_error: "IB Calc SW Allocation is required",
  }),
  ib_calc_hw_allocation: z.coerce.number({
    invalid_type_error: "IB Calc HW Allocation must be a number",
    required_error: "IB Calc HW Allocation is required",
  }),
  sold_as_sw_allocation: z.coerce.number({
    invalid_type_error: "Sold As SW Allocation must be a number",
    required_error: "Sold As SW Allocation is required",
  }),
  sold_as_hw_allocation: z.coerce.number({
    invalid_type_error: "Sold As HW Allocation must be a number",
    required_error: "Sold As HW Allocation is required",
  }),
  agreement_start_date: z.string().refine(testDate, {
    message: "Invalid agreement start date. Expected format: DD/MM/YYYY",
  }),
  agreement_end_date: z.string().refine(testDate, {
    message: "Invalid agreement end date. Expected format: DD/MM/YYYY",
  }),
  booking_country: z.string({
    required_error: "Booking Country is required",
    invalid_type_error: "Booking Country must be text",
  }),
  cam_revenue_usd: currency,
});

export const ContractSchema = ContractBaseSchema;

export type TContractInput = z.input<typeof ContractSchema>;
export type TContractOutput = z.output<typeof ContractSchema>;

export type TMappedContractOutput = Omit<
  TContractOutput,
  | "booked_theater"
  | "sold_as_service_type"
  | "sold_as_pricing_type"
  | "buying_program_type"
> & {
  booked_theater: number;
  sold_as_service_type: number;
  sold_as_pricing_type: number;
  buying_program_type: number;
};
