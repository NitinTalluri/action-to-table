import { TDcTypes } from "~/domain/DcTypes/schema";
import { useDcTypes } from "~/hooks/dcTypes/useDcTypes";

type TableValues = TDcTypes[number]["mappings"];
export type AvailableTables = Array<
  Omit<TDcTypes[number]["mappings"][number], "is_deleted"> & {
    is_deleted: false;
  }
>;

type TUseTableTypeProps<T = string[]> = {
  table_names: T;
};

type TUseTableTypesSingleReturn = {
  all: TableValues;
  available: AvailableTables;
};

type TUseTableTypesReturn<T extends string[]> = Record<
  T[number],
  TUseTableTypesSingleReturn
>;

type TDcTableNames =
  | "dc_contract_asset_mgt_types"
  | "dc_contract_monitor_types"
  | "dc_contract_types"
  | "dc_engagement_sfc_types"
  | "dc_engagement_stakeholder_types"
  | "dc_sold_as_service_types"
  | "dc_theater"
  | "dc_pricing_model"
  | "dc_buying_programs"
  | "dc_bookings_user_role"
  | "dc_typ_disengage"
  | "dc_typ_signoff_method"
  | "dc_typ_signoff_event"
  | "dc_typ_sign_off_identity"
  | "dc_typ_defer_signoff_reason"
  | "dc_typ_root_causes"
  | "dc_typ_booking_type"
  | "dc_typ_booking_override"
  | "dc_sdp_typ_anchor_date"
  | "dc_sdp_typ_anchor_date_iterator"
  | "dc_sdp_typ_task_completion_reason"
  | "dc_sales_level";

export const useTableTypes = <T extends TDcTableNames[]>(
  props: TUseTableTypeProps<T>,
): Readonly<TUseTableTypesReturn<T>> => {
  const { table_names } = props;
  const dcTypes = useDcTypes();

  const tableTypes = table_names.reduce((acc, table_name) => {
    const table = dcTypes.find((dcType) => dcType.table_name === table_name);
    if (!table) {
      throw new Error(`Table ${table_name} not found in dcTypes`);
    }
    return {
      ...acc,
      [table_name]: {
        all: table.mappings,
        available: table.mappings.filter(
          (mapping) => !mapping.is_deleted,
        ) as AvailableTables,
      },
    };
  }, {} as TUseTableTypesReturn<T>);

  return tableTypes;
};

const fetchDistinctAvailableValue = (
  available: AvailableTables,
  value: string,
) => {
  return available.find((a) => a.value.toLowerCase() === value.toLowerCase());
};

export const useContractAssetMgtTableTypes = () => {
  const { dc_contract_asset_mgt_types } = useTableTypes({
    table_names: ["dc_contract_asset_mgt_types"],
  });
  return dc_contract_asset_mgt_types;
};

export const useDcContractTableTypes = () => {
  const { dc_contract_types } = useTableTypes({
    table_names: ["dc_contract_types"],
  });
  return dc_contract_types;
};

export const useEngagementSfcTableTypes = () => {
  const { dc_engagement_sfc_types } = useTableTypes({
    table_names: ["dc_engagement_sfc_types"],
  });
  return dc_engagement_sfc_types;
};

export const useStakeHolderTableTypes = () => {
  const { dc_engagement_stakeholder_types } = useTableTypes({
    table_names: ["dc_engagement_stakeholder_types"],
  });
  return dc_engagement_stakeholder_types;
};

export const useSoldAsServiceTableTypes = () => {
  const { dc_sold_as_service_types } = useTableTypes({
    table_names: ["dc_sold_as_service_types"],
  });

  const serviceTypeUnknown = fetchDistinctAvailableValue(
    dc_sold_as_service_types.available,
    "UNKNOWN",
  );

  const serviceTypePremiumHWSW = fetchDistinctAvailableValue(
    dc_sold_as_service_types.available,
    "PREMIUM(HW/SW)",
  );

  const serviceTypeStandardSW = fetchDistinctAvailableValue(
    dc_sold_as_service_types.available,
    "STANDARD(SW)",
  );

  const serviceTypeStandardHW = fetchDistinctAvailableValue(
    dc_sold_as_service_types.available,
    "STANDARD(HW)",
  );

  return {
    ...dc_sold_as_service_types,
    serviceTypeUnknown,
    serviceTypePremiumHWSW,
    serviceTypeStandardSW,
    serviceTypeStandardHW,
  };
};

export const useTheaterTableTypes = () => {
  const { dc_theater } = useTableTypes({ table_names: ["dc_theater"] });
  return dc_theater;
};

export const usePricingModelTableTypes = () => {
  const { dc_pricing_model } = useTableTypes({
    table_names: ["dc_pricing_model"],
  });
  return dc_pricing_model;
};

export const useBuyingProgramTableTypes = () => {
  const { dc_buying_programs } = useTableTypes({
    table_names: ["dc_buying_programs"],
  });

  const cxeaDesignated = fetchDistinctAvailableValue(
    dc_buying_programs.available,
    "CXEA - Designated",
  );

  const cxeaScale = fetchDistinctAvailableValue(
    dc_buying_programs.available,
    "CXEA - Scale",
  );

  return {
    ...dc_buying_programs,
    cxeaDesignated,
    cxeaScale,
  };
};

export const useBookingsUserRolesTableTypes = () => {
  const { dc_bookings_user_role } = useTableTypes({
    table_names: ["dc_bookings_user_role"],
  });

  const camUnknown = fetchDistinctAvailableValue(
    dc_bookings_user_role.available,
    "unknown",
  );

  const camPrimary = fetchDistinctAvailableValue(
    dc_bookings_user_role.available,
    "cam-primary",
  );

  const camSecondary = fetchDistinctAvailableValue(
    dc_bookings_user_role.available,
    "cam-secondary",
  );

  const camBackup = fetchDistinctAvailableValue(
    dc_bookings_user_role.available,
    "cam-backup",
  );

  const camTraining = fetchDistinctAvailableValue(
    dc_bookings_user_role.available,
    "cam-training",
  );

  return {
    ...dc_bookings_user_role,
    camPrimary,
    camSecondary,
    camBackup,
    camTraining,
    camUnknown,
  };
};

export const useMonitorTableTypes = () => {
  const { dc_contract_monitor_types } = useTableTypes({
    table_names: ["dc_contract_monitor_types"],
  });
  return dc_contract_monitor_types;
};

export const useDisengagementTableType = () => {
  const { dc_typ_disengage } = useTableTypes({
    table_names: ["dc_typ_disengage"],
  });
  return dc_typ_disengage;
};

export const useSignoffTableTypes = () => {
  const { dc_typ_signoff_method } = useTableTypes({
    table_names: ["dc_typ_signoff_method"],
  });
  return dc_typ_signoff_method;
};

export const useSignOffIdentityTableTypes = () => {
  const { dc_typ_sign_off_identity } = useTableTypes({
    table_names: ["dc_typ_sign_off_identity"],
  });
  return dc_typ_sign_off_identity;
};

export const useDeferSignoffReasonTableTypes = () => {
  const { dc_typ_defer_signoff_reason } = useTableTypes({
    table_names: ["dc_typ_defer_signoff_reason"],
  });
  return dc_typ_defer_signoff_reason;
};

export const useAnchorDateTableTypes = () => {
  const { dc_sdp_typ_anchor_date } = useTableTypes({
    table_names: ["dc_sdp_typ_anchor_date"],
  });
  return dc_sdp_typ_anchor_date;
};

export const useCycleDateIteratorTableTypes = () => {
  const { dc_sdp_typ_anchor_date_iterator } = useTableTypes({
    table_names: ["dc_sdp_typ_anchor_date_iterator"],
  });
  return dc_sdp_typ_anchor_date_iterator;
};

export const useClosedTaskReasonTableTypes = () => {
  const { dc_sdp_typ_task_completion_reason } = useTableTypes({
    table_names: ["dc_sdp_typ_task_completion_reason"],
  });
  return dc_sdp_typ_task_completion_reason;
};

export const useSalesLevelTableTypes = () => {
  const { dc_sales_level } = useTableTypes({
    table_names: ["dc_sales_level"],
  });
  return dc_sales_level;
};

export const useBookingOverrideTableTypes = () => {
  const { dc_typ_booking_override } = useTableTypes({
    table_names: ["dc_typ_booking_override"],
  });
  return dc_typ_booking_override;
};
