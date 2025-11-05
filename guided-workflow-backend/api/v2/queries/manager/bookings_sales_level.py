from collections import Counter
from typing import TYPE_CHECKING

from snowflake.sqlalchemy import MergeInto
from sqlalchemy import Integer, String, and_, column, func, values

from api.v2.orm.bookings import V2BookingContracts, V2SalesLevel
from api.v2.queries import QueryMembership

if TYPE_CHECKING:
    from sqlmodel import Session

    from api.v2.models.manager.bookings import (
        SalesLevelAssignmentError,
        V2BulkSalesLevelAssignmentResponse,
        V2SalesLevelAssignment,
    )


def _build_sales_level_validation_query(assignments: list["V2SalesLevelAssignment"]):
    """Build the QueryMembership validation query without executing it"""
    booking_contracts = list({item.booking_contract for item in assignments})
    sales_level_ids = list({item.sales_level_id for item in assignments})

    membership_query = QueryMembership()
    membership_query.add_orm_membership(V2BookingContracts, booking_contracts)
    membership_query.add_orm_membership(V2SalesLevel, sales_level_ids)

    return membership_query.build()


def _build_sales_level_merge_statement(
    assignments: list["V2SalesLevelAssignment"], requestor_cco_id: str
):
    """Build the MERGE statement for bulk sales level assignment without executing it"""
    rows_data = [
        (item.booking_contract, item.sales_level_id, requestor_cco_id)
        for item in assignments
    ]

    source_values = values(
        column("booking_contract", Integer),
        column("sales_level_id", Integer),
        column("updated_by", String),
        name="sales_level_assignments",
    ).data(rows_data)

    merge_statement = MergeInto(
        target=V2BookingContracts.__table__,
        source=source_values,
        on=and_(
            V2BookingContracts.booking_contract == source_values.c.booking_contract,
            V2BookingContracts.__table__.c.is_deleted == "F",
        ),
    )

    merge_statement.when_matched_then_update().values(
        sales_level_id=source_values.c.sales_level_id,
        updated_by=source_values.c.updated_by,
        update_dtm=func.current_timestamp(),
    )

    return merge_statement


def bulk_assign_sales_levels(
    session: "Session",
    assignments: list["V2SalesLevelAssignment"],
    requestor_cco_id: str,
) -> "V2BulkSalesLevelAssignmentResponse":
    """Bulk assign sales levels to booking contracts using SQLAlchemy values() construct"""

    def make_error(
        booking_contract: int, sales_level_id: int, message: str
    ) -> "SalesLevelAssignmentError":
        return {
            "booking_contract": booking_contract,
            "sales_level_id": sales_level_id,
            "message": message,
        }

    def detect_duplicates(
        payload: list["V2SalesLevelAssignment"],
    ) -> list["SalesLevelAssignmentError"]:
        if len({item.booking_contract for item in payload}) == len(payload):
            return []

        bc_counts = Counter(item.booking_contract for item in payload)
        duplicates = [bc for bc, count in bc_counts.items() if count > 1]
        errors = []
        for dup in duplicates:
            dup_items = [item for item in payload if item.booking_contract == dup]
            for item in dup_items:
                errors.append(
                    make_error(
                        item.booking_contract,
                        item.sales_level_id,
                        "Duplicate booking contract in payload",
                    )
                )
        return errors

    # Early return if no assignments to process
    if not assignments:
        from api.v2.models.manager.bookings import V2BulkSalesLevelAssignmentResponse

        return V2BulkSalesLevelAssignmentResponse(
            has_errors=False, errors=[], assignments={}
        )

    # Step 1: Check for duplicate booking contracts
    assignment_results = {}
    errors = detect_duplicates(assignments)

    # If we have duplicates, return errors immediately
    if errors:
        from api.v2.models.manager.bookings import V2BulkSalesLevelAssignmentResponse

        return V2BulkSalesLevelAssignmentResponse(
            has_errors=True, errors=errors, assignments=assignment_results
        )

    # Step 2: Validate booking contracts and sales levels using QueryMembership
    validation_query = _build_sales_level_validation_query(assignments)
    missing_ids = session.exec(validation_query).all()  # type: ignore
    for missing_id, model_type in missing_ids:
        field_name = (
            "booking_contract"
            if model_type == "V2BookingContracts"
            else "sales_level_id"
        )
        entity_name = (
            "Booking contract" if model_type == "V2BookingContracts" else "Sales level"
        )

        for item in assignments:
            if getattr(item, field_name) == missing_id:
                errors.append(
                    make_error(
                        item.booking_contract,
                        item.sales_level_id,
                        f"{entity_name} {missing_id} does not exist",
                    )
                )

    if errors:
        from api.v2.models.manager.bookings import V2BulkSalesLevelAssignmentResponse

        return V2BulkSalesLevelAssignmentResponse(
            has_errors=True, errors=errors, assignments=assignment_results
        )

    # Step 3 & 4: Build and execute MERGE statement
    merge_statement = _build_sales_level_merge_statement(assignments, requestor_cco_id)
    session.exec(merge_statement)  # type: ignore

    # Build successful assignment mapping
    for item in assignments:
        assignment_results[item.booking_contract] = item.sales_level_id

    from api.v2.models.manager.bookings import V2BulkSalesLevelAssignmentResponse

    return V2BulkSalesLevelAssignmentResponse(
        has_errors=len(errors) > 0, errors=errors, assignments=assignment_results
    )


__all__ = [
    "bulk_assign_sales_levels",
]
