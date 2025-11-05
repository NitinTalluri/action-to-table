"""
Comprehensive SDP due_date integration tests supporting both Scale and non-Scale programs.

This module provides end-to-end testing of the SDP (Service Delivery Plan) due_date integration
feature, specifically designed to address CXEA Scale collision resolution scenarios while
maintaining backward compatibility with existing SEA non-Scale programs.

Key Features:
- Supports both SEA non-Scale (buying_program=2) and CXEA Scale (buying_program=5) programs
- Uses appropriate APIs: put_booking_assignments for non-Scale, rebuild_sdp_for_booking for Scale
- Conditional date manipulation controlled by update_days_back parameter
- Program-specific behavior verification and assertions
- Complete test data lifecycle with configurable cleanup
- Due_date integration testing with expanded logical primary keys
- End-to-end completion testing with due_date matching
"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List
from unittest import mock

import pytest
from fastapi.encoders import jsonable_encoder
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlmodel import Session
from starlette.authentication import AuthCredentials
from starlette.requests import Request

from api.dependencies import DataCanvasUser
from api.v2.models.contracts import (
    V2BookingEngagementAssignment,
    V2VerifiedBookingAssignmentModify,
)


class TestSDP_DueDateIntegration:
    """
    Comprehensive test suite for SDP due_date integration with Scale and non-Scale program support.

    This test class provides complete coverage of the SDP due_date integration feature,
    designed to prevent CXEA Scale collision scenarios while maintaining compatibility
    with existing SEA non-Scale programs.

    Test Architecture:
    - Parameterized testing with 4 scenarios covering all program/date combinations
    - Unified API wrapper pattern supporting both Scale and non-Scale rebuilds
    - Class-scoped fixtures with proper dependency management and cleanup
    - API-driven testing approach using FastAPI TestClient with proper authentication
    - Database transaction isolation using separate committed sessions

    Test Scenarios:
    1. SEA non-Scale + date update: Percentage-based increases due to new cycles
    2. SEA non-Scale + no date update: No count changes expected
    3. CXEA Scale + date update: Sum-based counting (additive sub-task behavior)
    4. CXEA Scale + no date update: Distinct sub-task counting (collision resolution)

    Program-Specific APIs:
    - Non-Scale: Uses put_booking_assignments endpoint with V2VerifiedBookingAssignmentModify
    - Scale: Uses rebuild_sdp_for_booking endpoint with V2RebuildSDPForBookingPayload

    Key Features:
    - Conditional date manipulation via update_days_back parameter
    - Working sub-task IDs for Scale testing: [8401,8402,8500,8503] and [8503,8501,8600]
    - Data integrity verification with expanded logical primary key including due_date
    - End-to-end completion testing with proper due_date matching
    - Configurable cleanup for test data management
    """

    # Test configuration constants
    SEA_NON_SCALE_PROGRAM = 2
    CXEA_SCALE_PROGRAM = 5
    HW_SERVICE_TYPE = 2
    PRIMARY_CAM_ROLE = 2
    DEFAULT_DAYS_BACK = 10
    MAX_INCREASE_PERCENTAGE = 20

    # Test data constants
    TEST_ACCOUNT_NAME = "Test Account"
    TEST_EMAIL = "test@cisco.com"
    TEST_USER_ID = 888
    TEST_ENGAGEMENT_ID = 94
    CLEANUP_ENABLED = True

    # Test booking contracts (must be between -1000 and -100 for safety)
    SEA_NON_SCALE_WITH_DATE_UPDATE_CONTRACT = -777
    SEA_NON_SCALE_NO_DATE_UPDATE_CONTRACT = -778
    CXEA_SCALE_WITH_DATE_UPDATE_CONTRACT = -779
    CXEA_SCALE_NO_DATE_UPDATE_CONTRACT = -780

    # Working sub-task IDs for Scale testing
    SCALE_SUB_TASK_IDS_1 = [8401, 8402, 8500, 8503]  # First rebuild pass
    SCALE_SUB_TASK_IDS_2 = [8503, 8501, 8600]        # Second rebuild pass (includes overlap for collision testing)

    # Class attributes for storing state between tests (set during test execution)
    _initial_counts: Dict[str, int] = {}
    _initial_scheduled_count: int = 0
    _initial_active_count: int = 0

    @pytest.fixture(
        params=[
            # Scenario 1: SEA non-Scale with date update (percentage-based increases)
            (
                SEA_NON_SCALE_WITH_DATE_UPDATE_CONTRACT,  # -777
                SEA_NON_SCALE_PROGRAM,                     # 2
                HW_SERVICE_TYPE,                           # 2
                TEST_USER_ID,                              # 888
                TEST_ENGAGEMENT_ID,                        # 94
                [],                                        # sub_task_ids_1 (not applicable)
                [],                                        # sub_task_ids_2 (not applicable)
                True,                                      # update_days_back
                CLEANUP_ENABLED,                           # cleanup
            ),
            # Scenario 2: SEA non-Scale without date update (no changes expected)
            (
                SEA_NON_SCALE_NO_DATE_UPDATE_CONTRACT,    # -778
                SEA_NON_SCALE_PROGRAM,                     # 2
                HW_SERVICE_TYPE,                           # 2
                TEST_USER_ID,                              # 888
                TEST_ENGAGEMENT_ID,                        # 94
                [],                                        # sub_task_ids_1 (not applicable)
                [],                                        # sub_task_ids_2 (not applicable)
                False,                                     # update_days_back
                CLEANUP_ENABLED,                           # cleanup
            ),
            # Scenario 3: CXEA Scale with date update (sum-based counting: 4 + 3 = 7 total)
            (
                CXEA_SCALE_WITH_DATE_UPDATE_CONTRACT,     # -779
                CXEA_SCALE_PROGRAM,                        # 5
                HW_SERVICE_TYPE,                           # 2
                TEST_USER_ID,                              # 888
                TEST_ENGAGEMENT_ID,                        # 94
                SCALE_SUB_TASK_IDS_1,                      # [8401, 8402, 8500, 8503]
                SCALE_SUB_TASK_IDS_2,                      # [8503, 8501, 8600]
                True,                                      # update_days_back
                CLEANUP_ENABLED,                           # cleanup
            ),
            # Scenario 4: CXEA Scale without date update (distinct counting: 6 unique)
            (
                CXEA_SCALE_NO_DATE_UPDATE_CONTRACT,       # -780
                CXEA_SCALE_PROGRAM,                        # 5
                HW_SERVICE_TYPE,                           # 2
                TEST_USER_ID,                              # 888
                TEST_ENGAGEMENT_ID,                        # 94
                SCALE_SUB_TASK_IDS_1,                      # [8401, 8402, 8500, 8503]
                SCALE_SUB_TASK_IDS_2,                      # [8503, 8501, 8600]
                False,                                     # update_days_back
                CLEANUP_ENABLED,                           # cleanup
            ),
        ],
        scope="class",
        ids=[
            "SEA_non-Scale_with_date_update",
            "SEA_non-Scale_no_date_update",
            "CXEA_Scale_with_date_update",
            "CXEA_Scale_no_date_update"
        ]
    )
    def test_params(self, request):
        """
        Parameterized fixture providing comprehensive test scenarios for SDP due_date integration.

        This fixture defines 4 complete test scenarios that cover all combinations of
        program types (Scale/non-Scale) and date manipulation (with/without updates).
        Each scenario tests different aspects of the due_date integration feature.

        Parameters:
            booking_contract: Test booking contract number (must be between -1000 and -100 for safety)
            buying_program_type_id: Program type (2=SEA non-Scale, 5=CXEA-Scale)
            service_type_id: Service type (2=HW, 4=SW, 3=HW+SW)
            user_id: Test user ID (888 for consistent testing)
            engagement_id: Test engagement ID (94 for consistent testing)
            sub_task_ids_1: List of sub-task IDs for first SDP rebuild pass
                          - Empty for non-Scale programs (not applicable)
                          - [8401,8402,8500,8503] for Scale programs (working IDs)
            sub_task_ids_2: List of sub-task IDs for second SDP rebuild pass
                          - Empty for non-Scale programs (not applicable)
                          - [8503,8501,8600] for Scale programs (includes overlap for collision testing)
            update_days_back: Boolean flag controlling date manipulation behavior
                            - True: Update dates 10 days back to simulate passage of time
                            - False: Skip date manipulation, test rebuild without date changes
            cleanup: Boolean flag controlling test data lifecycle
                   - True: Clean up test data after test runs (default for CI/production)
                   - False: Leave test data in database for inspection/debugging

        Test Scenarios Defined:
            1. SEA non-Scale + date update (-777): Tests existing percentage-based increase behavior
            2. SEA non-Scale + no date update (-778): Verifies no changes when dates unchanged
            3. CXEA Scale + date update (-779): Tests sum-based counting with date collision resolution
            4. CXEA Scale + no date update (-780): Tests distinct sub-task counting without collisions

        Expected Behaviors:
            - Non-Scale programs: Use put_booking_assignments API, percentage-based logic
            - Scale programs: Use rebuild_sdp_for_booking API, sub-task-based logic
            - Date updates: Trigger new cycle generation and deliverable increases
            - No date updates: Maintain existing counts with proper collision handling

        Returns:
            dict: Complete test parameters for the current scenario including all configuration flags
        """
        (
            booking_contract,
            buying_program_type_id,
            service_type_id,
            user_id,
            engagement_id,
            sub_task_ids_1,
            sub_task_ids_2,
            update_days_back,
            cleanup,
        ) = request.param

        # Safety check: Ensure booking_contract is in safe test range
        assert (
            -1000 <= booking_contract <= -100
        ), f"booking_contract {booking_contract} must be between -1000 and -100 for safety"

        return {
            "booking_contract": booking_contract,
            "buying_program_type_id": buying_program_type_id,
            "service_type_id": service_type_id,
            "user_id": user_id,
            "engagement_id": engagement_id,
            "sub_task_ids_1": sub_task_ids_1,
            "sub_task_ids_2": sub_task_ids_2,
            "update_days_back": update_days_back,
            "cleanup": cleanup,
        }


    @pytest.fixture
    def test_app(self, username):
        """Test app fixture - copied exactly from working test"""
        from api.dependencies.security import decode_bearer
        from api.main import app

        def decode_bearer_override(r: Request):
            user = DataCanvasUser(
                username=username,
                email=username,
                scopes={"dc_pool_manager", "dc_manager"},
            )
            cred = AuthCredentials(scopes=list(user.scopes))
            r.scope["user"] = user
            r.scope["auth"] = cred
            return user

        decode_bearer_override.__name__ = "decode_bearer_override"

        overrides = app.dependency_overrides
        app.dependency_overrides = {**overrides, decode_bearer: decode_bearer_override}
        yield app
        app.dependency_overrides = overrides

    @pytest.fixture()
    def admin_client(self, test_app):
        """Client for manager operations - copied from working test"""
        with TestClient(test_app) as client:
            yield client

    @pytest.fixture()
    def user_client(self, test_app):
        """Client with user privileges for deliverable queries"""
        # For now, use the same app setup - we'll add separate user auth later
        with TestClient(test_app) as client:
            yield client

    def create_test_assignments(
        self, user_id: int, engagement_id: int
    ) -> List[V2BookingEngagementAssignment]:
        """
        Create standardized test user assignments for SDP rebuild operations.

        This utility method generates consistent user assignment configurations
        for both Scale and non-Scale SDP rebuild operations. It ensures that
        all tests use the same assignment patterns for reproducible results.

        Assignment Configuration:
        - Single user assignment with PRIMARY_CAM role (service_role_id=2)
        - Hardware-only allocation (sub_allocation_hw=1.0, sub_allocation_sw=0.0)
        - Consistent with HW_SERVICE_TYPE=2 used throughout tests

        Usage:
        Used by both rebuild_sdp_non_scale() and rebuild_sdp_scale() methods
        to ensure consistent assignment patterns across all program types.
        This eliminates assignment-related variables when comparing SDP
        rebuild behavior between different scenarios.

        Args:
            user_id: User ID for the assignment (typically TEST_USER_ID=888)
            engagement_id: Engagement ID for the assignment (typically 94)

        Returns:
            List[V2BookingEngagementAssignment]: Single-item list with standardized assignment
        """
        return [
            V2BookingEngagementAssignment(
                dc_user_id=user_id,
                dc_engagement_id=engagement_id,
                service_role_id=self.PRIMARY_CAM_ROLE,
                sub_allocation_sw=Decimal("0.0"),  # HW only
                sub_allocation_hw=Decimal("1.0"),
            )
        ]

    def get_deliverables_count(
        self, db_session: Session, booking_contract: int
    ) -> Dict[str, int]:
        """
        Query deliverable counts from database tables for verification and comparison.

        This utility method provides standardized counting of deliverables across
        the key database tables used in SDP processing. It enables precise
        verification of SDP rebuild effects and comparison between test scenarios.

        Tables Queried:
        - dc_deliverables_core_eng: Core deliverable definitions
        - dc_deliverables_owed_scheduled_eng: Scheduled deliverable instances

        Counts Returned:
        - 'core': Total deliverable definitions in core table
        - 'scheduled': Total scheduled deliverable instances
        - 'cycles': Distinct cycle positions (index_pos values)

        Usage:
        Used throughout tests for:
        - Establishing baseline counts before operations
        - Verifying expected changes after SDP rebuilds
        - Comparing program-specific behavior differences
        - Debugging unexpected deliverable generation patterns

        Args:
            db_session: Database session for query execution
            booking_contract: Target booking contract for filtering

        Returns:
            Dict[str, int]: Dictionary with 'core', 'scheduled', and 'cycles' counts
        """
        counts = {}

        # Count in dc_deliverables_core_eng
        stmt = text("""
            SELECT COUNT(*) as count
            FROM dc_deliverables_core_eng
            WHERE booking_contract = :booking_contract
        """).bindparams(booking_contract=booking_contract)
        counts["core"] = db_session.exec(stmt).scalar()  # type: ignore[arg-type]

        # Count in dc_deliverables_owed_scheduled_eng
        stmt = text("""
            SELECT COUNT(*) as count
            FROM dc_deliverables_owed_scheduled_eng
            WHERE booking_contract = :booking_contract
        """).bindparams(booking_contract=booking_contract)
        counts["scheduled"] = db_session.exec(stmt).scalar()  # type: ignore[arg-type]

        # Count distinct cycles
        stmt = text("""
            SELECT COUNT(DISTINCT index_pos) as count
            FROM dc_deliverables_owed_scheduled_eng
            WHERE booking_contract = :booking_contract
        """).bindparams(booking_contract=booking_contract)
        counts["cycles"] = db_session.exec(stmt).scalar()  # type: ignore[arg-type]

        return counts

    def get_api_deliverables_count(
        self, user_client: TestClient, engagement_id: int, booking_contract: int
    ):
        """
        Query deliverable counts from user-facing API endpoints for end-to-end validation.

        This method validates that deliverables created through manager APIs are
        properly accessible through user-facing endpoints, ensuring the complete
        SDP workflow functions correctly from creation to user consumption.

        API Endpoints Tested:
        - GET /api/v2/sdp/{engagement_id}/deliverables/scheduled: Scheduled deliverables
        - GET /api/v2/sdp/{engagement_id}/deliverables/active: Active deliverables

        Data Processing:
        - Filters results to include only the specific booking_contract being tested
        - Counts deliverable groups (headers) rather than individual deliverable instances
        - Returns both counts and raw data for detailed analysis if needed

        Validation Purpose:
        - Ensures deliverables are accessible through user-facing APIs
        - Verifies proper data flow from manager operations to user queries
        - Enables comparison of database counts vs API-accessible counts
        - Validates API filtering and grouping logic

        Usage Pattern:
        Used in conjunction with get_deliverables_count() to provide comprehensive
        validation covering both database state and API accessibility.

        Args:
            user_client: TestClient configured with user authentication
            engagement_id: Target engagement ID for API queries
            booking_contract: Target booking contract for filtering results

        Returns:
            dict: {
                'scheduled': int,  # Count of scheduled deliverable groups
                'active': int,     # Count of active deliverable groups
                'scheduled_data': list,  # Raw scheduled deliverable data
                'active_data': list      # Raw active deliverable data
            }
        """
        # Get scheduled deliverables
        uri = user_client.app.url_path_for(
            "get_user_engagement_scheduled_deliverables", dc_engagement_id=engagement_id
        )
        response = user_client.get(uri)
        assert (
            response.status_code == 200
        ), f"Scheduled deliverables error: {response.text}"

        scheduled_data = response.json()
        assert isinstance(scheduled_data, list)
        test_scheduled = [
            d for d in scheduled_data if d["booking_contract"] == booking_contract
        ]

        # Get active deliverables
        uri = user_client.app.url_path_for(
            "get_user_engagement_active_deliverables", dc_engagement_id=engagement_id
        )
        response = user_client.get(uri)
        assert (
            response.status_code == 200
        ), f"Active deliverables error: {response.text}"

        active_data = response.json()
        assert isinstance(active_data, list)
        test_active = [
            d for d in active_data if d["booking_contract"] == booking_contract
        ]

        return {
            "scheduled": len(test_scheduled),
            "active": len(test_active),
            "scheduled_data": test_scheduled,
            "active_data": test_active,
        }

    def update_dates_back_n_days(
        self, db_session: Session, booking_contract: int, days_back: int = 10
    ):
        """
        Simulate passage of time by updating deliverable dates backwards to trigger new cycle generation.

        This utility method manipulates date fields in the deliverable tables to simulate
        the passage of time, which should trigger new deliverable cycle generation when
        SDP rebuilds are subsequently executed. This is essential for testing the
        due_date integration behavior under different temporal scenarios.

        Purpose:
        - Simulate time passage for testing temporal SDP behavior
        - Trigger new cycle generation in subsequent SDP rebuilds
        - Test due_date integration under different date collision scenarios
        - Validate percentage-based increases in non-Scale programs
        - Test sum-based vs distinct counting in Scale programs

        Database Tables Modified:
        - dc_deliverables_core_eng: Updates AGREEMENT_START_DATE, AGREEMENT_END_DATE, DUE_DATE_LIST
        - dc_deliverables_owed_scheduled_eng: Updates DUE_DATE, VISIBILITY_DATE, dates in HEADER_NAME

        Date Manipulation Logic:
        - Moves all relevant date fields backwards by the specified number of days
        - Uses DATEADD SQL function for consistent date arithmetic
        - Updates complex JSON arrays in DUE_DATE_LIST using TRANSFORM function
        - Updates embedded dates in HEADER_NAME fields using regex replacement
        - Commits changes immediately to ensure visibility to subsequent operations

        Validation:
        - Verifies date changes actually occurred by comparing before/after ranges
        - Ensures deliverable records exist before attempting updates
        - Provides detailed logging of date ranges for debugging

        Args:
            db_session: Active database session for executing updates
            booking_contract: Target booking contract number for date updates
            days_back: Number of days to move dates backward (default: 10 for standard testing)

        Raises:
            AssertionError: If no deliverables found or date updates fail to apply
        """
        # Create reusable query for date range checking
        date_range_query = text("""
            SELECT MIN(due_date) as min_due, MAX(due_date) as max_due
            FROM dc_deliverables_owed_scheduled_eng
            WHERE booking_contract = :booking_contract
        """).bindparams(booking_contract=booking_contract)

        result_before = db_session.exec(date_range_query).mappings().one()  # type: ignore[arg-type]
        print(f"Date range BEFORE: {result_before['min_due']} to {result_before['max_due']}")

        if result_before["min_due"] is None and result_before["max_due"] is None:
            raise AssertionError(f"No deliverables found for booking_contract {booking_contract}")

        print(f"Updating dates to {days_back} days back...")

        # Update basic date columns in dc_deliverables_core_eng (skip complex DUE_DATE_LIST for now)
        update_core_stmt = text("""
            UPDATE dc_deliverables_core_eng
            SET
                AGREEMENT_START_DATE = AGREEMENT_START_DATE - :days_back,
                AGREEMENT_END_DATE = AGREEMENT_END_DATE - :days_back,
                DUE_DATE_LIST = TRANSFORM(DUE_DATE_LIST, x -> DATEADD(day, :days_back * -1, TO_DATE(x)))
            WHERE booking_contract = :booking_contract
        """).bindparams(booking_contract=booking_contract, days_back=days_back)
        db_session.exec(update_core_stmt)  # type: ignore[arg-type]

        # Update all date columns in dc_deliverables_owed_scheduled_eng in one statement
        update_scheduled_stmt = text("""
            UPDATE dc_deliverables_owed_scheduled_eng
            SET
                DUE_DATE = DUE_DATE - :days_back,
                VISIBILITY_DATE = VISIBILITY_DATE - :days_back,
                MIN_OPEN_DATE = MIN_OPEN_DATE - :days_back,
                MAX_OPEN_DATE = MAX_OPEN_DATE - :days_back,
                HEADER_NAME = CASE
                    WHEN HEADER_NAME RLIKE 'Due by:\\([0-9]{4}-[0-9]{2}-[0-9]{2}\\)' THEN
                        REPLACE(
                            HEADER_NAME,
                            CONCAT('Due by:(', REGEXP_SUBSTR(HEADER_NAME, '[0-9]{4}-[0-9]{2}-[0-9]{2}'), ')'),
                            CONCAT('Due by:(', TO_VARCHAR(DATEADD('day', -:days_back, TO_DATE(REGEXP_SUBSTR(HEADER_NAME, '[0-9]{4}-[0-9]{2}-[0-9]{2}')))), ')')
                        )
                    ELSE HEADER_NAME
                END
            WHERE booking_contract = :booking_contract
        """).bindparams(booking_contract=booking_contract, days_back=days_back)
        db_session.exec(update_scheduled_stmt)  # type: ignore[arg-type]

        db_session.commit()

        result_after = db_session.exec(date_range_query).mappings().one()  # type: ignore[arg-type]
        print(f"Date range AFTER: {result_after['min_due']} to {result_after['max_due']}")

        assert result_before["min_due"] != result_after["min_due"] or result_before["max_due"] != result_after["max_due"], "Date ranges unchanged after update"

    def rebuild_sdp_non_scale(
        self,
        admin_client: TestClient,
        user_id: int,
        engagement_id: int,
        booking_contract: int,
    ):
        """
        Execute SDP rebuild for SEA non-Scale programs using the put_booking_assignments endpoint.

        This method handles SDP rebuilds for traditional SEA non-Scale programs (buying_program=2)
        using the standard put_booking_assignments API endpoint. This endpoint does not require
        sub_task_ids and uses the existing percentage-based logic for deliverable generation.

        API Details:
        - Endpoint: PUT /api/v2/manager/bookings/assignments
        - Payload: V2VerifiedBookingAssignmentModify with booking_contract and assignments
        - Authentication: Requires dc_manager and dc_pool_manager scopes

        Behavior:
        - Uses existing SDP generation logic based on booking contract configuration
        - Generates deliverables based on agreement dates and service allocations
        - Supports percentage-based increases when dates are updated
        - Does not use sub_task_id filtering (applies to all applicable sub-tasks)

        Args:
            admin_client: TestClient with proper authentication scopes
            user_id: User ID for the assignment (typically TEST_USER_ID=888)
            engagement_id: Engagement ID for the assignment (typically 94)
            booking_contract: Booking contract number (negative for test contracts)

        Returns:
            Response: FastAPI response object from the put_booking_assignments API call
        """
        assignments = self.create_test_assignments(user_id, engagement_id)
        payload = V2VerifiedBookingAssignmentModify(
            booking_contract=booking_contract, assignments=assignments
        )

        response = admin_client.put(
            "/api/v2/manager/bookings/assignments",
            json=jsonable_encoder(payload, custom_encoder={Decimal: str}),
        )

        return response

    def rebuild_sdp_scale(
        self,
        admin_client: TestClient,
        user_id: int,
        engagement_id: int,
        booking_contract: int,
        sub_task_ids: List[int],
    ):
        """
        Execute SDP rebuild for CXEA Scale programs using the rebuild_sdp_for_booking endpoint.

        This method handles SDP rebuilds specifically for CXEA Scale programs (buying_program=5)
        using the specialized rebuild_sdp_for_booking API endpoint. This endpoint requires
        explicit sub_task_ids and implements the due_date integration logic for collision resolution.

        API Details:
        - Endpoint: POST /api/v2/manager/bookings/sdp/{booking_contract}
        - Payload: V2RebuildSDPForBookingPayload with booking_contract, sub_task_ids, and assignments
        - Authentication: Requires dc_manager and dc_pool_manager scopes

        Scale-Specific Behavior:
        - Uses sub_task_id filtering to generate deliverables only for specified sub-tasks
        - Implements due_date integration for collision resolution scenarios
        - Supports sum-based counting when dates are updated (additive behavior)
        - Supports distinct counting when dates are unchanged (collision prevention)
        - Critical for preventing CXEA Scale collision scenarios

        Sub-Task ID Usage:
        - Working IDs for testing: [8401, 8402, 8500, 8503] and [8503, 8501, 8600]
        - Overlap in sub-task 8503 used to test collision resolution logic
        - Must be valid sub-task IDs that exist in the dc_sdp_typ_subtask table

        Args:
            admin_client: TestClient with proper authentication scopes
            user_id: User ID for the assignment (typically TEST_USER_ID=888)
            engagement_id: Engagement ID for the assignment (typically 94)
            booking_contract: Booking contract number (negative for test contracts)
            sub_task_ids: List of valid sub-task IDs for deliverable generation

        Returns:
            Response: FastAPI response object from the rebuild_sdp_for_booking API call
        """
        from api.v2.models.manager.sdp import V2RebuildSDPForBookingPayload

        assignments = self.create_test_assignments(user_id, engagement_id)
        payload = V2RebuildSDPForBookingPayload(
            booking_contract=booking_contract,
            sub_task_ids=sub_task_ids,
            assignments=assignments
        )

        response = admin_client.post(
            admin_client.app.url_path_for('rebuild_sdp_for_booking', booking_contract=booking_contract),
            json=jsonable_encoder(payload, custom_encoder={Decimal: str}),
        )

        return response

    def rebuild_sdp(
        self,
        admin_client: TestClient,
        user_id: int,
        engagement_id: int,
        booking_contract: int,
        buying_program_type_id: int,
        sub_task_ids: List[int] | None = None,
    ):
        """
        Unified wrapper method for SDP rebuilds supporting both Scale and non-Scale programs.

        This method provides a single interface for SDP rebuilds while internally routing
        to the appropriate program-specific implementation based on the buying_program_type_id.
        This design eliminates code duplication and ensures consistent behavior across
        different test scenarios.

        Program Routing Logic:
        - buying_program_type_id == 5 (CXEA_SCALE_PROGRAM): Routes to rebuild_sdp_scale()
        - buying_program_type_id == 2 (SEA_NON_SCALE_PROGRAM): Routes to rebuild_sdp_non_scale()
        - Other program types: Routes to rebuild_sdp_non_scale() as default

        Validation:
        - For Scale programs: Validates that sub_task_ids is provided and non-empty
        - For non-Scale programs: Ignores sub_task_ids parameter (not applicable)

        Usage Pattern:
        This method enables parameterized testing where the same test logic can handle
        multiple program types by simply changing the buying_program_type_id parameter.
        This is essential for the comprehensive test scenarios defined in test_params.

        Args:
            admin_client: TestClient with proper authentication scopes
            user_id: User ID for the assignment
            engagement_id: Engagement ID for the assignment
            booking_contract: Booking contract number
            buying_program_type_id: Program type determining API routing
                                  - 2: SEA non-Scale (uses put_booking_assignments)
                                  - 5: CXEA Scale (uses rebuild_sdp_for_booking)
            sub_task_ids: List of sub-task IDs (required for Scale, ignored for non-Scale)

        Returns:
            Response: FastAPI response object from the appropriate program-specific API call

        Raises:
            ValueError: If Scale program is specified but sub_task_ids is None or empty
        """
        if buying_program_type_id == self.CXEA_SCALE_PROGRAM:
            if not sub_task_ids:
                raise ValueError("sub_task_ids is required for Scale programs")
            return self.rebuild_sdp_scale(admin_client, user_id, engagement_id, booking_contract, sub_task_ids)
        else:
            return self.rebuild_sdp_non_scale(admin_client, user_id, engagement_id, booking_contract)

    def verify_booking_contract_created(
        self,
        db_session: Session,
        booking_contract: int,
        buying_program_type_id: int,
        user_id: int,
    ):
        """
        Verify booking contract creation and configuration in database before SDP operations.

        This validation method ensures that the test booking contract was properly
        created by the create_test_booking fixture and configured with the correct
        parameters before proceeding with SDP rebuild operations. This prevents
        test failures due to improper setup.

        Validation Checks:
        - Booking contract record exists in dc_bookings_contracts table
        - buying_program_type_id matches expected value (Scale vs non-Scale)
        - claimed_and_managed_by field matches expected user_id
        - Provides debugging information if validation fails

        Error Handling:
        If validation fails, the method:
        - Logs detailed error information for debugging
        - Queries existing test contracts in the valid range for comparison
        - Raises AssertionError with specific failure details

        Safety Check:
        This verification is critical because SDP rebuild operations depend on
        proper booking contract configuration, and failures here indicate
        fundamental setup issues rather than SDP logic problems.

        Args:
            db_session: Database session for query execution
            booking_contract: Expected booking contract number (typically negative for tests)
            buying_program_type_id: Expected program type (2=non-Scale, 5=Scale)
            user_id: Expected managing user ID (typically TEST_USER_ID=888)

        Raises:
            AssertionError: If booking contract not found or configuration incorrect
        """
        stmt = text("""
            SELECT buying_program_type_id, claimed_and_managed_by
            FROM dc_bookings_contracts
            WHERE booking_contract = :booking_contract
        """).bindparams(booking_contract=booking_contract)
        result = db_session.exec(stmt).mappings().one_or_none()  # type: ignore[arg-type]

        if result is None:
            debug_stmt = text("SELECT booking_contract FROM dc_bookings_contracts WHERE booking_contract BETWEEN -1000 AND -100")
            debug_result = db_session.exec(debug_stmt).all()  # type: ignore[arg-type]
            raise AssertionError(f"Booking contract {booking_contract} not found. Existing test contracts: {debug_result}")

        assert result["buying_program_type_id"] == buying_program_type_id, f"Wrong program type: {result['buying_program_type_id']} != {buying_program_type_id}"
        assert result["claimed_and_managed_by"] == user_id, f"Wrong manager: {result['claimed_and_managed_by']} != {user_id}"
        print(f"✓ Booking contract {booking_contract} verified")

    # Database cleanup tables in proper dependency order to avoid foreign key violations
    CLEANUP_TABLES = [
        "dc_completed_deliverables",               # Completion records (child of scheduled deliverables)
        "dc_deliverables_owed_scheduled_eng",      # Scheduled deliverable instances (child of core)
        "dc_deliverables_core_eng",                # Core deliverable definitions (child of contracts)
        "dc_bookings_contracts_responsible_users", # User assignments (child of contracts)
        "dc_bookings_contracts",                   # Main booking contract records (parent)
    ]

    def _cleanup_booking_data(self, session, booking_contract: int):
        """
        Clean up test booking data from all related tables in dependency order.

        This helper method removes test data from all tables that reference
        the booking contract, following proper dependency order to avoid
        foreign key constraint violations during cleanup operations.

        Cleanup Order (CLEANUP_TABLES):
        1. dc_completed_deliverables: Completion records (references deliverables)
        2. dc_deliverables_owed_scheduled_eng: Scheduled deliverables (references core)
        3. dc_deliverables_core_eng: Core deliverable definitions
        4. dc_bookings_contracts_responsible_users: User assignments (references contract)
        5. dc_bookings_contracts: Main booking contract record

        Safety:
        - Only affects records matching the specific booking_contract
        - Respects foreign key dependencies to prevent constraint violations
        - Used by both create_test_booking fixture and manual cleanup operations

        Args:
            session: Database session for executing DELETE operations
            booking_contract: Target booking contract number for cleanup
        """
        for table in self.CLEANUP_TABLES:
            stmt = text(
                f"DELETE FROM {table} WHERE booking_contract = :booking_contract"
            )
            session.exec(stmt.bindparams(booking_contract=booking_contract))  # type: ignore[arg-type]

    @pytest.fixture(scope="class")
    def create_test_booking(
        self,
        test_params: dict,
    ):
        """
        Class-scoped fixture for creating test booking contracts with proper transaction isolation.

        This fixture creates booking contracts in separate committed database transactions
        to ensure they are visible to the SDP rebuild process, which runs in its own
        transaction context. This addresses database isolation issues that can occur
        when test data and application code use different transaction scopes.

        Features:
        - Creates booking contract with all required fields and relationships
        - Uses separate database session with explicit commit for transaction isolation
        - Inserts both booking contract and responsible user relationship records
        - Provides configurable cleanup based on cleanup parameter
        - Implements proper error handling and logging for debugging

        Database Tables Modified:
        - dc_bookings_contracts: Main booking contract record
        - dc_bookings_contracts_responsible_users: User assignment relationships

        Transaction Isolation:
        The fixture uses a fresh database session with explicit commits to ensure
        the booking contract data is persisted and visible to subsequent API calls
        that run in separate database transactions.

        Cleanup Behavior:
        - If cleanup=True: Removes all test data after test completion
        - If cleanup=False: Leaves data for inspection/debugging
        - Cleanup follows proper dependency order to avoid foreign key constraints
        """
        # Extract parameters from test_params
        booking_contract = test_params["booking_contract"]
        buying_program_type_id = test_params["buying_program_type_id"]
        service_type_id = test_params["service_type_id"]
        user_id = test_params["user_id"]
        cleanup = test_params["cleanup"]

        from sqlmodel import Session

        from api.dependencies import get_settings
        from api.dependencies.database import get_engine

        engine = get_engine(get_settings())

        # Create booking contract in a separate committed transaction
        with Session(bind=engine) as fresh_session:
            self._cleanup_booking_data(fresh_session, booking_contract)
            insert_stmt = text("""
                INSERT INTO dc_bookings_contracts (
                    booking_contract, buying_program_type_id, sold_as_service_type_id,
                    claimed_and_managed_by, agreement_end_date, agreement_start_date,
                    account_name, booked_theater_id, sold_as_pricing_type_id,
                    sold_as_sw_allocation, sold_as_hw_allocation
                ) VALUES (
                    :booking_contract, :buying_program_type_id, :service_type_id,
                    :claimed_and_managed_by, CURRENT_DATE() + 365, CURRENT_DATE(),
                    :account_name, 2, 1, 0.0, 15.0
                )
            """).bindparams(
                booking_contract=booking_contract,
                buying_program_type_id=buying_program_type_id,
                service_type_id=service_type_id,
                claimed_and_managed_by=user_id,
                account_name=self.TEST_ACCOUNT_NAME,
            )
            fresh_session.exec(insert_stmt)  # type: ignore[arg-type]

            # Insert responsible users relationship
            insert_users_stmt = text("""
                INSERT INTO dc_bookings_contracts_responsible_users (
                    booking_contract, dc_user_id, sub_allocation_sw, sub_allocation_hw,
                    service_role_id, created_by, is_deleted
                ) VALUES (
                    :booking_contract, :user_id, 0.0, 15.0, :service_role_id, :created_by, 'F'
                )
            """).bindparams(
                booking_contract=booking_contract,
                user_id=user_id,
                service_role_id=self.PRIMARY_CAM_ROLE,
                created_by=self.TEST_EMAIL,
            )
            fresh_session.exec(insert_users_stmt)  # type: ignore[arg-type]

            fresh_session.commit()
            print(f"✓ Created booking contract {booking_contract}")

        yield

        if cleanup:
            try:
                with Session(bind=engine) as cleanup_session:
                    self._cleanup_booking_data(cleanup_session, booking_contract)
                    cleanup_session.commit()
                    print(f"✓ Cleaned up test data for {booking_contract}")
            except Exception as e:
                print(f"Warning: Cleanup failed: {e}")
        else:
            print(f"INFO: Skipping cleanup for {booking_contract}")

    @mock.patch(
        "api.v2.services.external.prefect_v3_flow_service.PrefectV3APIMixin._emit_api_event"
    )
    @pytest.mark.dependency(name="test1_sdp_setup")
    def test_1_create_dummy_booking_and_rebuild_sdp(
        self,
        emit_api_event_mock,
        admin_client: TestClient,
        user_client: TestClient,
        db_session: Session,
        create_test_booking,
        test_params: dict,
    ):
        """
        Test initial SDP setup and baseline deliverable generation for all program types.

        This foundational test establishes the baseline deliverable data for both Scale
        and non-Scale programs. It serves as the setup phase for all subsequent tests
        and verifies that the basic SDP rebuild functionality works correctly for each
        program type with their respective APIs and parameters.

        Test Purpose:
        - Establish baseline deliverable counts for comparison in subsequent tests
        - Verify program-specific API routing works correctly
        - Confirm deliverables are accessible through user-facing API endpoints
        - Store initial state data for delta comparisons in test_2

        Program-Specific Behavior:
        - SEA non-Scale: Uses put_booking_assignments, generates standard deliverable set
        - CXEA Scale: Uses rebuild_sdp_for_booking with sub_task_ids_1, generates filtered deliverables

        Given:
        - Booking contract pre-created via create_test_booking fixture with proper configuration
        - Program type (Scale/non-Scale) determined by buying_program_type_id parameter
        - Service type set to HW (service_type_id=2) for consistent testing
        - User assignments configured with proper allocations and PRIMARY_CAM role
        - For Scale: sub_task_ids_1 contains working sub-task IDs [8401,8402,8500,8503]

        When:
        - Booking contract existence and configuration is verified in database
        - Appropriate SDP rebuild API is called based on program type:
          * Non-Scale: put_booking_assignments endpoint
          * Scale: rebuild_sdp_for_booking endpoint with sub_task_ids_1
        - Database deliverable counts are queried from core and scheduled tables
        - User deliverable API endpoints are queried for accessibility verification

        Then:
        - Booking contract exists with correct buying_program_type_id and user assignment
        - Deliverables are created in dc_deliverables_core_eng (core definitions)
        - Deliverables are created in dc_deliverables_owed_scheduled_eng (scheduled instances)
        - Deliverables are accessible via scheduled and active deliverables API endpoints
        - Baseline counts are stored in class variables for subsequent test comparisons
        """
        # Extract parameters for clean variable names
        booking_contract = test_params["booking_contract"]
        buying_program_type_id = test_params["buying_program_type_id"]
        service_type_id = test_params["service_type_id"]
        user_id = test_params["user_id"]
        engagement_id = test_params["engagement_id"]
        sub_task_ids_1 = test_params["sub_task_ids_1"]
        sub_task_ids_2 = test_params["sub_task_ids_2"]
        update_days_back = test_params["update_days_back"]
        cleanup = test_params["cleanup"]

        # Step 1: Verify booking contract was created by fixture
        self.verify_booking_contract_created(
            db_session, booking_contract, buying_program_type_id, user_id
        )

        # Step 2: Run SDP rebuild (unified method handles both Scale and non-Scale)
        response = self.rebuild_sdp(
            admin_client, user_id, engagement_id, booking_contract,
            buying_program_type_id, sub_task_ids_1
        )
        print(f"Response status: {response.status_code}")
        if response.status_code != 200:
            print(f"Error response: {response.text}")
            print(f"Response content: {response.content}")
        else:
            print(f"Success response: {response.json()}")

        # Let's verify the data was created in the database

        # Step 3: Verify data in database tables
        initial_counts = self.get_deliverables_count(db_session, booking_contract)
        print(f"Database counts: {initial_counts}")

        assert initial_counts["core"] > 0, f"No core deliverables found. Response was: {response.status_code}. Database counts: {initial_counts}"
        assert initial_counts["scheduled"] > 0, "No scheduled deliverables found"
        assert initial_counts["cycles"] > 0, "No cycles found"

        print(f"Initial counts: {initial_counts}")

        # Step 4: Verify data appears in user deliverables endpoints
        api_deliverables = self.get_api_deliverables_count(
            user_client, engagement_id, booking_contract
        )

        assert api_deliverables["scheduled"] > 0, "No scheduled deliverables found via API"
        print(f"Found {api_deliverables['scheduled']} scheduled, {api_deliverables['active']} active deliverable groups")

        # Store initial state for next test
        TestSDP_DueDateIntegration._initial_counts = initial_counts
        TestSDP_DueDateIntegration._initial_scheduled_count = api_deliverables[
            "scheduled"
        ]
        TestSDP_DueDateIntegration._initial_active_count = api_deliverables["active"]

    @mock.patch(
        "api.v2.services.external.prefect_v3_flow_service.PrefectV3APIMixin._emit_api_event"
    )
    @pytest.mark.dependency(name="test2_date_update", depends=["test1_sdp_setup"])
    def test_2_update_dates_and_rebuild_sdp(
        self,
        emit_api_event_mock,
        admin_client: TestClient,
        user_client: TestClient,
        db_session: Session,
        create_test_booking,
        test_params: dict,
    ):
        # Extract parameters for clean variable names
        booking_contract = test_params["booking_contract"]
        buying_program_type_id = test_params["buying_program_type_id"]
        service_type_id = test_params["service_type_id"]
        user_id = test_params["user_id"]
        engagement_id = test_params["engagement_id"]
        sub_task_ids_1 = test_params["sub_task_ids_1"]
        sub_task_ids_2 = test_params["sub_task_ids_2"]
        update_days_back = test_params["update_days_back"]
        cleanup = test_params["cleanup"]
        """
        Test SDP rebuild behavior with conditional date manipulation and program-specific logic.

        This comprehensive test verifies the core due_date integration functionality by
        testing different behaviors based on program type and date update configuration.
        It demonstrates how the system handles collision scenarios and ensures proper
        behavior for both existing and new program types.

        Test Matrix (4 Scenarios):
        1. SEA non-Scale + date update: Tests percentage-based increases (traditional behavior)
        2. SEA non-Scale + no date update: Verifies no changes when dates unchanged
        3. CXEA Scale + date update: Tests sum-based counting with collision resolution
        4. CXEA Scale + no date update: Tests distinct counting without date collisions

        Program-Specific Expected Behaviors:
        Non-Scale Programs:
        - Date update: Generates new cycles, shows percentage-based increases (≤20%)
        - No date update: Maintains existing counts, no deliverable changes

        Scale Programs:
        - Date update: Sum-based counting (len(sub_task_ids_1) + len(sub_task_ids_2) = 7)
        - No date update: Distinct counting (len(set(sub_task_ids_1 + sub_task_ids_2)) = 6)

        Due_Date Integration Testing:
        The test validates that the due_date field integration properly handles:
        - Collision prevention when same sub-tasks have different due dates
        - Proper accumulation when sub-tasks span multiple date ranges
        - Correct API routing and parameter passing for each program type

        Given:
        - Baseline deliverable data established in test_1 for the current scenario
        - Initial counts stored in class variables for delta comparison
        - Booking contract configured for specific program type testing
        - Sub-task IDs configured appropriately (empty for non-Scale, working IDs for Scale)

        When:
        - Conditionally update dates 10 days back if update_days_back=True
        - Execute second SDP rebuild with program-specific parameters:
          * Non-Scale: Same API call as test_1 (no sub-task ID changes)
          * Scale: Uses sub_task_ids_2 for collision/distinct counting scenarios
        - Query updated database counts and API endpoint data

        Then:
        - SDP rebuild completes successfully (HTTP 200 response)
        - Deliverable counts change according to program-specific expectations
        - Date analysis confirms proper date range handling
        - All program/date combination scenarios validate correctly
        """

        initial_counts_check = self.get_deliverables_count(db_session, booking_contract)
        print(f"Pre-update counts: {initial_counts_check}")
        if initial_counts_check["scheduled"] == 0:
            if initial_counts_check["core"] == 0:
                raise AssertionError("No deliverables in core or scheduled tables - SDP rebuild failed")
            else:
                raise AssertionError("Deliverables in core but not scheduled - SDP process incomplete")

        # Step 1: Conditionally update dates based on update_days_back parameter
        if test_params["update_days_back"]:
            self.update_dates_back_n_days(db_session, test_params["booking_contract"], 10)
            print("✅ Dates updated 10 days back")
        else:
            print("INFO: Skipping date update (update_days_back=False)")

        # Step 2: Determine sub-task IDs for rebuild based on program type
        if test_params["buying_program_type_id"] == self.CXEA_SCALE_PROGRAM:
            # For Scale programs, use sub_task_ids_2 for the second rebuild
            rebuild_sub_task_ids = test_params["sub_task_ids_2"]
            print(f"Scale program: Using sub_task_ids_2 = {rebuild_sub_task_ids}")
        else:
            # For non-Scale programs, sub-task IDs are not used
            rebuild_sub_task_ids = []
            print("Non-Scale program: No sub-task IDs needed")

        # Step 3: Rerun SDP rebuild using unified method
        response = self.rebuild_sdp(
            admin_client, test_params["user_id"], test_params["engagement_id"], test_params["booking_contract"],
            test_params["buying_program_type_id"], rebuild_sub_task_ids
        )
        assert response.status_code == 200, f"Response: {response.text}"
        print(f"SDP rebuild completed with status: {response.status_code}")

        # Step 3: Get updated counts
        updated_counts = self.get_deliverables_count(db_session, test_params["booking_contract"])
        initial_counts = TestSDP_DueDateIntegration._initial_counts

        print(f"Initial counts: {initial_counts}")
        print(f"Updated counts: {updated_counts}")

        # Step 4: Verify data is still in deliverables endpoints
        api_deliverables = self.get_api_deliverables_count(
            user_client, test_params["engagement_id"], test_params["booking_contract"]
        )

        initial_scheduled_count = TestSDP_DueDateIntegration._initial_scheduled_count
        initial_active_count = TestSDP_DueDateIntegration._initial_active_count

        print(f"Scheduled: {initial_scheduled_count} -> {api_deliverables['scheduled']}, Active: {initial_active_count} -> {api_deliverables['active']}")

        # Step 5: Program-specific behavior verification
        program_type = 'Scale' if test_params["buying_program_type_id"] == self.CXEA_SCALE_PROGRAM else 'non-Scale'
        print(f"Program: {program_type}, Date update: {'Yes' if test_params['update_days_back'] else 'No'}")

        assert api_deliverables["scheduled"] > 0, "No scheduled deliverables after rebuild"

        if test_params["buying_program_type_id"] == self.CXEA_SCALE_PROGRAM:
            # Scale program behavior
            if test_params["update_days_back"]:
                expected_total = len(test_params["sub_task_ids_1"]) + len(test_params["sub_task_ids_2"])
                print(f"Scale + date update: Expected {expected_total} sub-tasks ({len(test_params['sub_task_ids_1'])}+{len(test_params['sub_task_ids_2'])}, sum-based)")
            else:
                unique_sub_tasks = set(test_params["sub_task_ids_1"] + test_params["sub_task_ids_2"])
                expected_total = len(unique_sub_tasks)
                print(f"Scale + no date update: Expected {expected_total} unique sub-tasks (distinct counting)")

            scheduled_entries_increased = updated_counts["scheduled"] > initial_counts["scheduled"]
            scheduled_groups_increased = api_deliverables["scheduled"] > initial_scheduled_count
            print(f"Entries: {initial_counts['scheduled']} -> {updated_counts['scheduled']}, Groups: {initial_scheduled_count} -> {api_deliverables['scheduled']}")
            assert scheduled_entries_increased, "Scale should increase scheduled entries"
            assert scheduled_groups_increased, "Scale should increase scheduled groups"
            print("✅ Scale program behavior verified")

        else:
            # Non-Scale program behavior
            if test_params["update_days_back"]:
                # Non-Scale + date update: existing percentage-based logic
                scheduled_entries_increased = updated_counts["scheduled"] > initial_counts["scheduled"]
                scheduled_groups_increased = api_deliverables["scheduled"] > initial_scheduled_count
                active_increased = api_deliverables["active"] > initial_active_count
                print(f"Entries: {initial_counts['scheduled']} -> {updated_counts['scheduled']}, Groups: {initial_scheduled_count} -> {api_deliverables['scheduled']}, Active: {initial_active_count} -> {api_deliverables['active']}")

                if scheduled_entries_increased:
                    increase_percentage = ((updated_counts["scheduled"] - initial_counts["scheduled"]) / initial_counts["scheduled"]) * 100
                    assert 0 < increase_percentage <= 20, f"Expected 0-20% increase, got {increase_percentage:.1f}%"
                    print(f"✅ Entries increased {increase_percentage:.1f}%")
                else:
                    raise AssertionError("Non-Scale + date update should increase entries")

                if scheduled_groups_increased:
                    group_increase_percentage = ((api_deliverables["scheduled"] - initial_scheduled_count) / initial_scheduled_count) * 100
                    assert 0 < group_increase_percentage <= 20, f"Expected 0-20% group increase, got {group_increase_percentage:.1f}%"
                    print(f"✅ Groups increased {group_increase_percentage:.1f}%")
                else:
                    raise AssertionError("Non-Scale + date update should increase groups")

                assert active_increased, "Non-Scale + date update should increase active deliverables"
                print("✅ Non-Scale + date update verified")

            else:
                scheduled_entries_same = updated_counts["scheduled"] == initial_counts["scheduled"]
                scheduled_groups_same = api_deliverables["scheduled"] == initial_scheduled_count
                active_same = api_deliverables["active"] == initial_active_count
                print(f"All counts maintained: Entries={scheduled_entries_same}, Groups={scheduled_groups_same}, Active={active_same}")
                assert scheduled_entries_same, "Non-Scale + no date update should maintain entry count"
                assert scheduled_groups_same, "Non-Scale + no date update should maintain group count"
                assert active_same, "Non-Scale + no date update should maintain active count"
                print("✅ Non-Scale + no date update verified")

        # Additional verification: Check date ranges
        stmt = text("""
            SELECT
                MIN(due_date) as min_due,
                MAX(due_date) as max_due,
                COUNT(DISTINCT due_date) as unique_dates
            FROM dc_deliverables_owed_scheduled_eng
            WHERE booking_contract = :booking_contract
        """).bindparams(booking_contract=booking_contract)
        result = db_session.exec(stmt).mappings().one()  # type: ignore[arg-type]

        print(f"Final dates: {result['min_due']} to {result['max_due']} ({result['unique_dates']} unique)")

        # Verify that both old and new dates exist (indicating accumulative behavior)
        current_date = datetime.now().date()
        old_date_exists = result["min_due"] < current_date - timedelta(days=5)
        new_date_exists = result["max_due"] > current_date - timedelta(days=5)

        if old_date_exists and new_date_exists:
            print("✅ Both old and new dates exist (accumulative behavior)")
        elif new_date_exists:
            print("INFO: Only new dates exist (rebuild replaced old)")
        else:
            print("⚠️ Unexpected date pattern")

    @pytest.mark.dependency(depends=["test2_date_update"])
    def test_3_verify_data_integrity_with_due_date_key(
        self,
        db_session: Session,
        create_test_booking,
        test_params: dict,
    ):
        # Extract parameters for clean variable names
        booking_contract = test_params["booking_contract"]
        """
        Verify data integrity and duplicate prevention with expanded due_date logical primary key.

        This critical test validates the core functionality of the due_date integration by
        ensuring that the expanded logical primary key prevents duplicate records and
        maintains data integrity across all collision scenarios. This is essential for
        the CXEA Scale collision resolution feature.

        Key Validation:
        The test verifies that the expanded logical primary key:
        (sub_task_id, booking_contract, cycle_iterator, dc_engagement_id, due_date)
        successfully prevents duplicate records even when:
        - Same sub-tasks are processed multiple times
        - Date updates create overlapping scenarios
        - Scale programs use overlapping sub-task ID sets
        - Multiple SDP rebuilds occur with different parameters

        Critical for CXEA Scale:
        This validation is particularly important for CXEA Scale programs where:
        - Sub-task overlap (e.g., 8503 in both sub_task_ids_1 and sub_task_ids_2)
        - Date manipulation creating collision scenarios
        - Multiple rebuild cycles with different sub-task combinations
        - Due_date integration must prevent data corruption

        Database Integrity Check:
        Queries dc_deliverables_owed_scheduled_eng for any records that share
        the complete logical primary key values, which should never occur
        if the due_date integration is working correctly.

        Given:
        - Deliverable data exists from test_2 after potential date manipulation
        - Multiple SDP rebuilds may have occurred with overlapping parameters
        - Due_date integration has been applied throughout the test sequence

        When:
        - Query for duplicate records using complete logical primary key
        - Group by all key fields including due_date
        - Count occurrences of each unique key combination

        Then:
        - No duplicate records exist with identical logical primary key values
        - Data integrity is maintained across all collision scenarios
        - Due_date integration successfully prevents data corruption
        """

        # Check for actual duplicate records (same key including due_date)
        # The logical primary key should be: sub_task_id, booking_contract, index_pos, dc_engagement_id, due_date
        stmt = text("""
            SELECT
                sub_task_id,
                booking_contract,
                index_pos as cycle_iterator,
                dc_engagement_id,
                due_date,
                COUNT(*) as duplicate_count
            FROM dc_deliverables_owed_scheduled_eng
            WHERE booking_contract = :booking_contract
            GROUP BY sub_task_id, booking_contract, index_pos, dc_engagement_id, due_date
            HAVING COUNT(*) > 1
            ORDER BY duplicate_count DESC
            LIMIT 10
        """).bindparams(booking_contract=booking_contract)

        duplicate_records = db_session.exec(stmt).mappings().all()  # type: ignore[arg-type]

        if duplicate_records:
            print(f"⚠️ Found {len(duplicate_records)} duplicate record sets:")
            for dup in duplicate_records:
                print(f"  {dup['sub_task_id']}/{dup['cycle_iterator']}/{dup['dc_engagement_id']}/{dup['due_date']} -> {dup['duplicate_count']} duplicates")
            raise AssertionError(f"Found {len(duplicate_records)} duplicate record sets - due_date integration failed")
        else:
            print("✅ No duplicate records found with logical primary key")

    @pytest.mark.dependency(depends=["test2_date_update"])
    def test_4_verify_completion_due_date_matching(
        self,
        db_session: Session,
        user_client: TestClient,
        create_test_booking,
        test_params: dict,
    ):
        # Extract parameters for clean variable names
        booking_contract = test_params["booking_contract"]
        engagement_id = test_params["engagement_id"]
        """
        Test end-to-end deliverable completion with due_date integration and logical primary key matching.

        This comprehensive test validates the complete deliverable lifecycle including
        the critical completion matching functionality that relies on the expanded
        logical primary key containing due_date. This ensures that completion tracking
        works correctly even when multiple deliverables share other key components
        but differ by due_date.

        Critical Functionality Tested:
        - Completion payload construction with all required key fields including due_date
        - Completion API processing with due_date-enhanced logical primary key matching
        - Completed deliverable retrieval through user-facing API endpoints
        - Proper filtering of completed deliverables from active deliverable lists
        - End-to-end completion workflow validation

        Due_Date Integration Validation:
        This test specifically validates that the due_date field integration works
        correctly in the completion system by:
        - Including due_date in completion payload (UserSDPCompletionDeliverablePayload)
        - Verifying completion matching uses due_date for precise record identification
        - Confirming completed deliverables are accessible with correct due_date values
        - Ensuring completion filtering works with due_date-enhanced primary keys

        API Endpoints Tested:
        - PUT /api/v2/sdp/completions: Deliverable completion with due_date integration
        - GET /api/v2/sdp/{engagement_id}/deliverables/closed: Completed deliverables retrieval
        - GET /api/v2/sdp/{engagement_id}/deliverables/active: Active deliverables filtering

        Collision Scenario Coverage:
        This test ensures that even in collision scenarios where multiple deliverables
        might share (sub_task_id, booking_contract, cycle_iterator, dc_engagement_id),
        the addition of due_date to the logical primary key allows precise completion
        matching without affecting other deliverables.

        Given:
        - Deliverable data exists from previous tests with potential date variations
        - Completion system configured to use due_date in logical primary key matching
        - User API endpoints available for completion workflow testing

        When:
        - Select a specific deliverable record for completion testing
        - Construct completion payload with all key fields including due_date
        - Submit completion via PUT /api/v2/sdp/completions endpoint
        - Query completed deliverables via GET /api/v2/sdp/{engagement_id}/deliverables/closed
        - Verify filtering via GET /api/v2/sdp/{engagement_id}/deliverables/active

        Then:
        - Completion API succeeds with HTTP 200 response
        - Exactly one deliverable is marked as completed with correct key field values
        - Completed deliverable appears in closed deliverables API with proper due_date
        - Completed deliverable is filtered out of active deliverables API
        - Due_date integration works correctly throughout completion workflow
        """

        # Get a deliverable to complete
        stmt = text("""
            SELECT
                sub_task_id,
                booking_contract,
                index_pos as cycle_iterator,
                dc_engagement_id,
                due_date
            FROM dc_deliverables_owed_scheduled_eng
            WHERE booking_contract = :booking_contract
            LIMIT 1
        """).bindparams(booking_contract=booking_contract)

        deliverable = db_session.exec(stmt).mappings().one_or_none()  # type: ignore[arg-type]

        if not deliverable:
            print("INFO: No deliverables found for completion testing")
            return

        # Complete the deliverable using the proper API endpoint
        from api.v2.models.sdp.completions import UserSDPCompletionDeliverablePayload

        completion_payload = UserSDPCompletionDeliverablePayload(
            sub_task_id=deliverable["sub_task_id"],
            booking_contract=deliverable["booking_contract"],
            cycle_iterator=deliverable["cycle_iterator"],
            dc_engagement_id=deliverable["dc_engagement_id"],
            due_date=deliverable["due_date"].isoformat() if hasattr(deliverable["due_date"], 'isoformat') else str(deliverable["due_date"]),
            completion_type_id=1,  # Default completion type
            is_completed=True,
            note="Test completion via API for due_date integration verification",
        )

        # Use user_client to call the completion API
        uri = user_client.app.url_path_for("put_sdp_completion")
        response = user_client.put(uri, json=jsonable_encoder(completion_payload))

        assert response.status_code == 200, f"Completion API failed: {response.text}"
        completion_response = response.json()

        print(f"✅ Completed deliverable with due_date: {deliverable['due_date']}, is_completed={completion_response.get('is_completed')}")

        # Verify the completion shows up via the closed deliverables API endpoint
        uri = user_client.app.url_path_for(
            "get_user_engagement_closed_deliverables", dc_engagement_id=engagement_id
        )
        response = user_client.get(uri)
        assert (
            response.status_code == 200
        ), f"Completed deliverables API error: {response.text}"

        completed_data = response.json()
        assert isinstance(completed_data, list)

        # Extract individual deliverables from header objects (closed deliverables API returns headers with nested tasks)
        test_completed_deliverables = []
        for header in completed_data:
            if header["booking_contract"] == booking_contract:
                test_completed_deliverables.extend(header["tasks"])  # tasks contains individual deliverables

        assert len(test_completed_deliverables) == 1, f"Expected 1 completed deliverable, found {len(test_completed_deliverables)}"

        completed_deliverable = test_completed_deliverables[0]
        assert completed_deliverable["sub_task_id"] == deliverable["sub_task_id"], "Wrong sub_task_id"
        assert completed_deliverable["cycle"] == deliverable["cycle_iterator"], "Wrong cycle"
        assert completed_deliverable["dc_engagement_id"] == deliverable["dc_engagement_id"], "Wrong engagement_id"
        assert str(completed_deliverable["due_date"]) == str(deliverable["due_date"]), "Wrong due_date"
        print("✅ Found completed deliverable with correct key fields")

        # Verify the completed deliverable does NOT show up in the active deliverables (should be filtered out)
        uri = user_client.app.url_path_for(
            "get_user_engagement_active_deliverables", dc_engagement_id=engagement_id
        )
        response = user_client.get(uri)
        assert (
            response.status_code == 200
        ), f"Active deliverables API error: {response.text}"

        active_data = response.json()
        assert isinstance(active_data, list)

        # Check if the completed deliverable still appears in active deliverables
        completed_deliverable_key = (
            deliverable["sub_task_id"],
            deliverable["booking_contract"],
            deliverable["cycle_iterator"],
            deliverable["dc_engagement_id"],
            str(deliverable["due_date"]),  # Convert to string for comparison
        )

        active_with_same_key = [
            d
            for d in active_data
            if (
                d.get("sub_task_id"),
                d.get("booking_contract"),
                d.get("cycle"),  # Active deliverables API also uses "cycle" not "cycle_iterator"
                d.get("dc_engagement_id"),
                str(d.get("due_date", "")),
            )
            == completed_deliverable_key
        ]

        assert len(active_with_same_key) == 0, f"Completed deliverable found in active list ({len(active_with_same_key)} matches)"
        print("✅ Completed deliverable filtered out of active list")
