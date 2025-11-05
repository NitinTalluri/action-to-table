from __future__ import annotations

from enum import Enum
from typing import Literal


class TrueFalse(str, Enum):
    T = "T"
    F = "F"

    def __str__(self) -> str:
        return str.__str__(self)


class CanvasType(str, Enum):
    current_view_canvas = "current view canvas"
    sourced_file_canvas = "sourced file canvas"
    unified_view_canvas = "unified view canvas"

    def __str__(self) -> str:
        return str.__str__(self)


class CanvasStatus(str, Enum):
    running = "running"
    success = "success"
    stopped = "stopped"

    def __str__(self) -> str:
        return str.__str__(self)


class V2CanvasPredefinedFileNames(str, Enum):
    """Predefined files for canvas creation in current view"""

    smart_account = "SMART_ACCOUNT"
    baseline_tags = "BASELINE_TAGS"
    mce = "MCE"
    acat = "ACAT"
    contracts = "CONTRACTS"
    party = "PARTY"

    def __str__(self) -> str:
        return str.__str__(self)


TV2CanvasPredefinedFileNames = Literal[
    "SMART_ACCOUNT", "BASELINE_TAGS", "MCE", "ACAT", "CONTRACTS", "PARTY"
]
V2LinkType = Literal["acat_links", "mce_links", "party_links", "smart_links"]
V2AcatLinkType = Literal["acat_links"]
V2MceLinkType = Literal["mce_links"]
V2PartyLinkType = Literal["party_links"]
V2SmartLinkType = Literal["smart_links"]
V2TagsetOneToOneType = Literal["1:1"]


class UiEnum(str, Enum):
    acat_discovery = "acat-discovery"
    add_to_contract = "add-to-contract"
    bulk_tagging = "bulk-tagging"
    canvas_actions = "canvas-actions"
    collector_upload = "collector-upload"
    customer_upload = "customer-upload"
    disengagement = "disengagement"
    general_notification = "general-notification"
    generate_docusign_scope = "generate-docusign-scope"
    host_name_relink = "host-name-relink"
    host_name_site_moves = "host-name-site-moves"
    instance_tagging = "instance-tagging"
    log_signoff = "log-signoff"
    macd_upload = "macd-upload"
    macd_historical_upload = "macd-historical-upload"
    macd_audit = "macd-audit"
    renewal = "renewal"
    sea_upload = "sea-upload"
    serial_tagging = "serial-tagging"
    site_report = "site-report"
    snif_report = "snif-report"
    tag_history = "tag-history"

    def __str__(self) -> str:
        return str.__str__(self)


TUiEnum = Literal[
    "acat-discovery",
    "add-to-contract",
    "bulk-tagging",
    "canvas-actions",
    "collector-upload",
    "customer-upload",
    "disengagement",
    "general-notification",
    "generate-docusign-scope",
    "host-name-relink",
    "host-name-site-moves",
    "instance-tagging",
    "log-signoff",
    "macd",
    "macd-upload",
    "macd-historical-upload",
    "renewal",
    "sea-upload",
    "serial-tagging",
    "site-report",
    "snif-report",
    "tag-history",
]


class BookingContractType(str, Enum):
    new = "NEW"
    renewal = "RENEWAL"
    upsell = "UPSELL"

    def __str__(self) -> str:
        return str.__str__(self)


class VirtualBookingType(str, Enum):
    prospective = "prospective"
    cross_charge = "cross-charge"

    def __str__(self) -> str:
        return str.__str__(self)


class V2TagsetCardinality(str, Enum):
    one_to_one = "1:1"

    def __str__(self) -> str:
        return str.__str__(self)


class V2SupportStatus(str, Enum):
    unassigned = "unassigned"
    assigned = "assigned"
    closed = "closed"

    def __str__(self) -> str:
        return str.__str__(self)


class V2ConfigTagStrategy(str, Enum):
    config_null = "config-null"
    config_all = "config-all"
    null = "null"

    def __str__(self) -> str:
        return str.__str__(self)


class ExtractState(str, Enum):
    pending = "pending"
    processed = "processed"
    deleted = "deleted"

    def __str__(self) -> str:
        return str.__str__(self)


class DbSchema(str, Enum):
    dev = "CPS_DSCI_BR"
    prod = "CPS_DSCI_API"

    def __str__(self) -> str:
        return str.__str__(self)


TDbSchema = Literal["CPS_DSCI_BR", "CPS_DSCI_API"]
TEnv = Literal["prod", "dev"]

__all__ = [
    "BookingContractType",
    "CanvasStatus",
    "CanvasType",
    "DbSchema",
    "ExtractState",
    "TDbSchema",
    "TEnv",
    "TUiEnum",
    "TrueFalse",
    "UiEnum",
    "V2AcatLinkType",
    "V2CanvasPredefinedFileNames",
    "V2ConfigTagStrategy",
    "V2LinkType",
    "V2MceLinkType",
    "V2PartyLinkType",
    "V2SmartLinkType",
    "V2SupportStatus",
    "V2TagsetCardinality",
    "V2TagsetOneToOneType",
    "VirtualBookingType",
]
