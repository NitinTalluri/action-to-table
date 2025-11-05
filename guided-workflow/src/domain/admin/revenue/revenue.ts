import { z } from "zod";

const DateFormatRegex = /^\d{1,2}\/\d{1,2}\/\d{4}$/;
const testDate = (value: string) =>
  DateFormatRegex.test(value) && !isNaN(Date.parse(value));

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

const CellNumber = z.coerce
  .string()
  .nullish()
  .catch(null)
  .transform((val) => {
    if (val === undefined) {
      return null;
    }
    if (typeof val === "string") {
      try {
        return parseInt(val);
      } catch (e) {
        return null;
      }
    }

    return val;
  });

const CellDecimal = z.coerce
  .string()
  .nullish()
  .catch(null)
  .transform((val) => {
    if (val === undefined) {
      return null;
    }
    if (typeof val === "string") {
      const parsed = parseFloat(val);
      return isNaN(parsed) ? null : parsed;
    }
    return val;
  });

const RevenueSchemaBase = z.object({
  fiscal_period_id: CellString,
  fiscal_year: CellNumber,
  fiscal_quarter_id: CellString,
  sales_level_1: CellString,
  sales_level_2: CellString,
  sales_level_3: CellString,
  finance_sub_group_or_contract_type: CellString,
  mktg_part_id: CellString,
  finance_bu_or_service_category: CellString,
  contract_number: CellNumber,
  transaction_number: CellNumber,
  transaction_type: CellString,
  transaction_date: z
    .string()
    .refine(testDate, {
      message: "Invalid transaction date. Expected format: DD/MM/YYYY",
    })
    .nullable()
    .catch(null),
  contract_start_date: z
    .string()
    .refine(testDate, {
      message: "Invalid contract start date. Expected format: DD/MM/YYYY",
    })
    .nullable()
    .catch(null),
  contract_end_date: z
    .string()
    .refine(testDate, {
      message: "Invalid contract end date. Expected format: DD/MM/YYYY",
    })
    .nullable()
    .catch(null),
  contract_term: CellNumber,
  total_amount: CellDecimal,
});

export const HTECRevenueSchema = RevenueSchemaBase;
export const CXEARevenueSchema = RevenueSchemaBase.extend({
  subscription_id: CellString,
  end_customer_global_ultimate_name: CellString,
  invoice_amount: CellNumber,
  invoice_revenue: CellNumber,
  country: CellString,
  l1_sales_finance_hierarchy_code: CellString,
  l2_sales_finance_hierarchy_code: CellString,
  external_theater_name_l1: CellString,
  subscription_code: CellString,
});
export const COGSRevenueSchema = z.object({
  company: CellNumber,
  department: CellNumber,
  department_name: CellString,
  account: CellNumber,
  account_description: CellString,
  sub_account: CellNumber,
  sub_account_description: CellString,
  project: CellNumber,
  market_segment: CellString,
  fiscal_period: CellString,
  gl_je_number: CellNumber,
  gl_je_line_number: CellNumber,
  source: CellString,
  category: CellString,
  batch_name: CellString,
  gl_description: CellString,
  gl_date: CellString,
  invoice_ap_gl_date: CellString,
  invoice_ap_date: CellString,
  invoice: CellString,
  invoice_description: CellString,
  ban_id: CellNumber,
  description: CellString,
  vendor: CellString,
  po_number: CellString,
  buyer: CellString,
  vendor_inv_distributor_key: CellNumber,
  person_entered_by: CellString,
  transactional_currency_code: CellString,
  trx_to_func_exchange_rate: CellDecimal,
  transactional_currency_dr: CellDecimal,
  transactional_currency_cr: CellDecimal,
  transactional_currency_net: CellDecimal,
  ap_transactional_currency_net: CellDecimal,
  functional_currency_code: CellString,
  functional_currency_dr: CellDecimal,
  functional_currency_cr: CellDecimal,
  functional_currency_net: CellDecimal,
  ap_functional_currency_net: CellDecimal,
  usd_dr: CellDecimal,
  usd_cr: CellDecimal,
  usd_net: CellDecimal,
  ap_usd_net: CellDecimal,
  theater: CellString,
  category1: CellString,
  category2: CellString,
  fiscal_period_id: CellString,
});

export type THTECRevenueContract = z.infer<typeof HTECRevenueSchema>;
type THTECRevenueContractInput = z.input<typeof HTECRevenueSchema>;
type THTECRevenueContractOutput = z.output<typeof HTECRevenueSchema>;

export type TCXEARevenueContract = z.infer<typeof CXEARevenueSchema>;
type TCXEARevenueContractInput = z.input<typeof CXEARevenueSchema>;
type TCXEARevenueContractOutput = z.output<typeof CXEARevenueSchema>;

export type TCOGSRevenueContract = z.infer<typeof COGSRevenueSchema>;
type TCOGSRevenueContractInput = z.input<typeof COGSRevenueSchema>;
type TCOGSRevenueContractOutput = z.output<typeof COGSRevenueSchema>;

export const HTECRevenueArraySchema: z.ZodType<
  THTECRevenueContractOutput[],
  z.ZodTypeDef,
  THTECRevenueContractInput[]
> = z.array(HTECRevenueSchema);

export const CXEARevenueArraySchema: z.ZodType<
  TCXEARevenueContractOutput[],
  z.ZodTypeDef,
  TCXEARevenueContractInput[]
> = z.array(CXEARevenueSchema);

export const COGSRevenueArraySchema: z.ZodType<
  TCOGSRevenueContractOutput[],
  z.ZodTypeDef,
  TCOGSRevenueContractInput[]
> = z.array(COGSRevenueSchema);
