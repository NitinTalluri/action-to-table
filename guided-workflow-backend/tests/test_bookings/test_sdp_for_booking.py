from decimal import Decimal

import pytest
import random
from sqlalchemy import text
from fastapi.testclient import TestClient
from fastapi.encoders import jsonable_encoder
from pydantic import parse_obj_as, ValidationError
from starlette.authentication import AuthCredentials
from starlette.requests import Request
from unittest import mock

from api.v2.models.manager.sdp import V2RebuildSDPForBookingPayload, V2GetSDPForBooking
from api.v2.models.contracts import V2BookingEngagementAssignment
from api.dependencies import GetSessionDep

import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
logger.addHandler(handler)

def make_decimals_sum_to_one(n: int) -> list[Decimal]:
    """
    Generates a list of n random Decimal objects that sum to Decimal('1.0').
    """
    if n <= 0:
        return []

    cuts = sorted([Decimal(str(random.random())) for _ in range(n - 1)])
    all_points = [Decimal('0')] + cuts + [Decimal('1')]

    decimals = [all_points[i] - all_points[i-1] for i in range(1, len(all_points))]
    assert sum(decimals) == 1
    return decimals


@pytest.fixture()
def assignments(request) -> list[V2BookingEngagementAssignment]:
    """
    This fixture generates a list of V2BookingEngagementAssignment objects based on the provided data:
    - service_type_id: The type of service (HW, SW, or HW+SW).
    - dc_user_ids: A list of user IDs to assign to the engagement.
    - dc_engagement_id: The engagement ID to which the users are assigned.

    The fixture creates a list of assignments with the following characteristics:
    - Each user is assigned a sub-allocation for both HW and SW that sums to 1.0.
    - The first user is assigned as a PRIMARY CAM (service_role_id = 2),
      while the rest (if any) are assigned as SECONDARY CAMs (service_role_id = 3).
    """
    service_type_id = request.getfixturevalue('service_type_id')
    dc_user_ids = request.getfixturevalue('dc_user_ids')
    dc_engagement_id = request.getfixturevalue('dc_engagement_id')

    n = len(dc_user_ids)
    hw_allocations = make_decimals_sum_to_one(n)
    sw_allocations = make_decimals_sum_to_one(n)
    no_allocations = [Decimal("0.0")] * n

    match service_type_id:
        case 2: # HW
            sw_allocations=no_allocations
        case 4: # SW
            hw_allocations=no_allocations
        case _: # HW+SW
            pass

    assignments = [
        V2BookingEngagementAssignment(
            dc_user_id=user_id,
            dc_engagement_id=dc_engagement_id,
            service_role_id=3, # SECONDARY CAM
            sub_allocation_sw=sw,
            sub_allocation_hw=hw,
        )
        for user_id, sw, hw in zip(dc_user_ids, sw_allocations, hw_allocations)
    ]

    # make first user a PRIMARY CAM
    assignments[0].service_role_id = 2 # PRIMARY CAM
    return assignments


@pytest.fixture()
def prepare_booking_contract(db_session, request):
    """
    This fixture prepares the booking contract by updating it with the buying program type and service type.
    """
    booking_contract = request.getfixturevalue('booking_contract')
    buying_program_type_id = request.getfixturevalue('buying_program_type_id')
    service_type_id = request.getfixturevalue('service_type_id')
    stmt = text("""
       UPDATE dc_bookings_contracts
          SET buying_program_type_id = :buying_program_type_id,
              sold_as_service_type_id = :sold_as_service_type_id,
              agreement_end_date = CURRENT_DATE()
        WHERE booking_contract = :booking_contract
        """).bindparams(buying_program_type_id=buying_program_type_id,
                        sold_as_service_type_id=service_type_id,
                        booking_contract=booking_contract)
    db_session.exec(stmt)
    db_session.commit()


class TestSDPForBooking:
    @pytest.fixture
    def test_app(self, username):
        from api.main import app
        from api.dependencies.security import decode_bearer
        from api.dependencies import DataCanvasUser

        def decode_bearer_override(r: Request):
            user = DataCanvasUser(username=username, email=username, scopes={"dc_pool_manager"})
            cred = AuthCredentials(scopes=list(user.scopes))
            r.scope["user"] = user
            r.scope["auth"] = cred
            return user

        overrides = app.dependency_overrides
        app.dependency_overrides = {**overrides, decode_bearer: decode_bearer_override}
        yield app
        app.dependency_overrides = overrides

    @pytest.fixture()
    def client(self, test_app):
        with TestClient(test_app) as client:
            yield client


    @pytest.mark.parametrize("booking_contract", [-999999999699])
    def test_manager_gated_endpoint(self, booking_contract, client):
        # If manager is logged in, they should be able to access the endpoint

        response = client.get(client.app.url_path_for("get_sdp_for_booking", booking_contract=booking_contract))
        assert response.status_code < 400, f"Response: {response.text}"
        parse_obj_as(list[V2GetSDPForBooking], response.json())


    @pytest.mark.parametrize("booking_contract, dc_engagement_id, buying_program_type_id, sub_task_ids,"
                             "service_type_id, dc_user_ids",
                             [
                                 # # no subtasks raises ValidationError
                                 # (-999999999699, 94, 5, [], 2, [888]),
                                 # # non-Scale buying program raises RuntimeError
                                 # (-999999999699, 94, 2, [114, 115], 2, [888, 884, 423]),
                                 # no errors
                                 (-999999999699, 94, 5, [114, 115], 2, [888, 884, 423]),
                                 # (-999999999699, 94, 5, [114, 115], 3, [888, 884, 423]),
                                 # (-999999999699, 94, 5, [114, 115], 4, [888, 884, 423]),
                             ])
    def test_rebuild_sdp_for_booking(self, db_session: GetSessionDep, client: TestClient,
                                     booking_contract:int, buying_program_type_id:int, dc_engagement_id:int,
                                     sub_task_ids: list[int], service_type_id: int, dc_user_ids: list[int],
                                     assignments: list[V2BookingEngagementAssignment],
                                     prepare_booking_contract):
        """
        Tests the 'rebuild_sdp_for_booking' endpoint for various valid and invalid scenarios.

        Given:
        - A booking contract is pre-configured in the database via the `prepare_booking_contract` fixture.
        - A list of user assignments is generated by the `assignments` fixture.
        - The test is parameterized to cover different cases:
            - An empty `sub_task_ids` list to triggers a validation error.
            - A non-Scale `buying_program_type_id` to trigger a business logic error.
            - Valid configurations for HW, SW, and HW+SW service types.

        Action:
        - A `V2RebuildSDPForBookingPayload` is constructed with the test parameters.
        - A POST request is sent to the 'rebuild_sdp_for_booking' endpoint with the payload.

        Assertion:
        - For invalid inputs (empty sub-tasks, non-scale program), it asserts the expected exception or HTTP error response.
        - For valid requests, it asserts:
            - The HTTP status code is 200.
            - The response can be parsed into the expected Pydantic model.
            - The database state is correctly updated, verifying sub-task links and user assignments (counts, roles, and allocation sums).
        """

        logger.info(assignments)

        # Test payload
        if len(sub_task_ids) < 1:
            with pytest.raises(ValidationError):
                V2RebuildSDPForBookingPayload(booking_contract=booking_contract,
                                              sub_task_ids=sub_task_ids,
                                              assignments=assignments)
            return

        payload = V2RebuildSDPForBookingPayload(
            booking_contract=booking_contract,
            sub_task_ids=sub_task_ids,
            assignments=assignments
        )

        response = client.post(
            client.app.url_path_for('rebuild_sdp_for_booking', booking_contract=booking_contract),
            json=jsonable_encoder(payload, custom_encoder={Decimal: str}))

        if buying_program_type_id == 2:
            assert response.status_code == 500, f"Response: {response.text}"
            assert 'for CXEA-Scale only' in response.text, f"Response: {response.text}"
            return

        assert response.status_code == 200, f"Response: {response.text}"
        parse_obj_as(list[V2GetSDPForBooking], response.json())

        stmt = text("""
            SELECT BOOLAND_AGG(SUB_TASK_ID IN (:sub_task_ids))
              FROM dc_deliverables_core_eng
             WHERE booking_contract = :booking_contract
        """).bindparams(booking_contract=booking_contract, sub_task_ids=tuple(sub_task_ids))

        assert db_session.exec(stmt).scalar()

        match service_type_id:
            case 2: # HW
                expected_sw, expected_hw = 0, 1
            case 4: # SW
                expected_sw, expected_hw = 1, 0
            case _: # HW+SW
                expected_sw, expected_hw = 1, 1

        stmt = text("""
            SELECT count(1) cnt, sum(sub_allocation_sw) sw, sum(sub_allocation_hw) hw,
                   sum(case when service_role_id = 2 then 1 end) cnt_primary,
                   sum(case when service_role_id = 3 then 1 end) cnt_secondary
              FROM dc_bookings_contracts_responsible_users
             WHERE booking_contract = :booking_contract
               AND is_deleted = 'F'
               and dc_user_id IN (:dc_user_ids)
            """).bindparams(booking_contract=booking_contract,
                            dc_user_ids=dc_user_ids)
        results = db_session.exec(stmt).mappings().one_or_none()
        assert results is not None, "No results found for the query"
        assert results['cnt'] == len(dc_user_ids), "Count of users does not match the expected count"
        assert results['cnt_primary'] == 1, "Count of primary CAMs does not match 1"
        assert results['cnt_secondary'] == len(dc_user_ids) - results['cnt_primary'],\
            "Count of Secondary CAMs does not match"
        assert results['sw'] == expected_sw, "SW allocation does not match the expected value"
        assert results['hw'] == expected_hw, "HW allocation does not match the expected value"



    @pytest.mark.parametrize("booking_contract, dc_engagement_id, buying_program_type_id, sub_task_ids,"
                             "service_type_id, dc_user_ids",
                             [
                                 (-999999999699, 94, 5, [114, 115], 2, [888, 884, 423]),
                                 (-999999999699, 94, 5, [114, 115], 3, [888, 884, 423]),
                                 (-999999999699, 94, 5, [114, 115], 4, [888, 884, 423]),
                             ])
    def test_rebuild_sdp_for_booking_invalid_assignments(self, db_session: GetSessionDep, client: TestClient,
                                     booking_contract:int, buying_program_type_id:int, dc_engagement_id:int,
                                     sub_task_ids: list[int], service_type_id: int, dc_user_ids: list[int],
                                     assignments: list[V2BookingEngagementAssignment],
                                     prepare_booking_contract):
        """
        Tests the 'rebuild_sdp_for_booking' endpoint for cases with invalid assignments.

        This test specifically verifies that allocations not summing to 1.0 result in
        appropriate validation errors. The test introduces intentional random offsets
        to allocations and verifies the API returns 400 error responses with proper
        error messages based on the service type.

        Given:
        - A booking contract is pre-configured in the database.
        - Valid sub_task_ids and assignment list.
        - One of the allocations is modified to break the sum-to-one constraint.

        Action:
        - Modify allocations based on service type.
        - POST the payload to the rebuild_sdp_for_booking endpoint.

        Assertion:
        - The HTTP response code is 400 (Bad Request).
        - The error message mentions the specific allocation issue based on service type.
        - The actual allocation values are included in the error message.
        """

        def make_random_offset(current_value):
            # add a random offset to the current value, positive or negative
            offset = Decimal(random.uniform(-0.3, 0.3))
            current_value += offset

            # Ensure the result is always > 0
            while current_value < 0:
                current_value += Decimal(random.uniform(0.01, 0.3))
            return current_value

        # break total allocation to not sum to 1
        match service_type_id:
            case 2: # HW
                assignments[0].sub_allocation_hw = make_random_offset(assignments[0].sub_allocation_hw)
            case 4: # SW
                assignments[0].sub_allocation_sw = make_random_offset(assignments[0].sub_allocation_sw)
            case _: # HW+SW
                assignments[0].sub_allocation_hw = make_random_offset(assignments[0].sub_allocation_hw)
                assignments[0].sub_allocation_sw = make_random_offset(assignments[0].sub_allocation_sw)

        logger.info(assignments)
        actual_sw = str(sum([a.sub_allocation_sw for a in assignments]))
        actual_hw = str(sum([a.sub_allocation_hw for a in assignments]))
        logger.info("actual_sw=%s, actual_hw=%s", actual_sw, actual_hw)

        payload = V2RebuildSDPForBookingPayload(
            booking_contract=booking_contract,
            sub_task_ids=sub_task_ids,
            assignments=assignments
        )

        response = client.post(
            client.app.url_path_for('rebuild_sdp_for_booking', booking_contract=booking_contract),
            json=jsonable_encoder(payload, custom_encoder={Decimal: str}))

        assert response.status_code == 400, f"Response: {response.text}"

        match service_type_id:
            case 2: # HW
                assert 'HW allocations must sum to 1.0' in response.text, f"Response: {response.text}"
                assert actual_hw in response.text, f"Response: {response.text}"
            case 4: # SW
                assert 'SW allocations must sum to 1.0' in response.text, f"Response: {response.text}"
                assert actual_sw in response.text, f"Response: {response.text}"
            case _: # HW+SW
                assert 'HW and SW allocations must sum to 1.0' in response.text, f"Response: {response.text}"
                assert actual_hw in response.text, f"Response: {response.text}"
                assert actual_sw in response.text, f"Response: {response.text}"


    @pytest.mark.parametrize("booking_contract, dc_engagement_id, buying_program_type_id, sub_task_ids,"
                             "service_type_id, dc_user_ids",
                             [
                                 (-999999999699, 94, 5, [114, 115], 2, [888, 884, 423]),
                                 (-999999999699, 94, 5, [114, 115], 3, [888, 884, 423]),
                                 (-999999999699, 94, 5, [114, 115], 4, [888, 884, 423]),
                             ])
    def test_rebuild_sdp_for_booking_multiple_primary(self, db_session: GetSessionDep, client: TestClient,
                                     booking_contract:int, dc_engagement_id:int, buying_program_type_id:int,
                                     sub_task_ids: list[int], service_type_id: int, dc_user_ids: list[int],
                                     assignments: list[V2BookingEngagementAssignment],
                                     prepare_booking_contract):
        """
        Tests the 'rebuild_sdp_for_booking' endpoint when multiple Primary CAMs are assigned to the same engagement.

        This test validates that the API correctly rejects payloads where multiple users are
        assigned the Primary CAM role for the same engagement. The business logic requires
        exactly one Primary CAM per engagement.

        Given:
        - A booking contract is pre-configured in the database.
        - Valid sub_task_ids and assignment list.
        - All users in the assignments are set to have the Primary CAM role (service_role_id = 2).

        Action:
        - Modify all assignments to have Primary CAM role.
        - POST the payload to the rebuild_sdp_for_booking endpoint.

        Assertion:
        - The HTTP response code is 400 (Bad Request).
        - The error message indicates that only one Primary CAM role is allowed per engagement.
        """

        logger.info(assignments)
        actual_sw = str(sum([a.sub_allocation_sw for a in assignments]))
        actual_hw = str(sum([a.sub_allocation_hw for a in assignments]))
        logger.info("actual_sw=%s, actual_hw=%s", actual_sw, actual_hw)

        payload = V2RebuildSDPForBookingPayload(
            booking_contract=booking_contract,
            sub_task_ids=sub_task_ids,
            assignments=assignments
        )

        # set PRIMARY CAM for all assignments
        for ass in payload.assignments:
            ass.service_role_id = 2

        response = client.post(
            client.app.url_path_for('rebuild_sdp_for_booking', booking_contract=booking_contract),
            json=jsonable_encoder(payload, custom_encoder={Decimal: str}))

        assert response.status_code == 400, f"Response: {response.text}"
        assert 'one Primary-CAM role per engagement' in response.text, f"Response: {response.text}"


    @pytest.mark.parametrize("booking_contract, dc_engagement_id, buying_program_type_id, sub_task_ids,"
                             "service_type_id, dc_user_ids, dc_engagement_ids",
                             [
                                 (-999999999699, 94, 5, [114, 115], 2, [888, 884], [94, 20332]),
                             ])
    def test_rebuild_sdp_for_booking_multiple_engagements(self, db_session: GetSessionDep, client: TestClient,
                                     booking_contract:int, dc_engagement_id:int, buying_program_type_id:int,
                                     sub_task_ids: list[int], service_type_id: int, dc_user_ids: list[int],
                                     dc_engagement_ids: list[int],
                                     assignments: list[V2BookingEngagementAssignment],
                                     prepare_booking_contract):
        """
        Tests the 'rebuild_sdp_for_booking' endpoint with multiple engagements.

        This test verifies that the API correctly handles a scenario where multiple users
        are assigned Primary CAM roles across different engagements. Unlike the multiple primary
        test, this is a valid configuration because each engagement has exactly one Primary CAM.

        Given:
        - A booking contract is pre-configured in the database.
        - Valid sub_task_ids and assignment list.
        - Multiple engagements are provided in dc_engagement_ids.
        - Each assignment is updated to have a different engagement ID and set as Primary CAM.

        Action:
        - Modify assignments to assign different engagement IDs.
        - Set all assignments to have Primary CAM role.
        - POST the payload to the rebuild_sdp_for_booking endpoint.

        Assertion:
        - The HTTP response code is 200 (OK), indicating success.
        - This validates that multiple Primary CAMs are allowed when they're assigned to different engagements.
        """

        for ix, dc_engagement_id in enumerate(dc_engagement_ids):
            assignments[ix].dc_engagement_id=dc_engagement_id
            assignments[ix].service_role_id=2 # PRIMARY CAM

        logger.info(assignments)

        payload = V2RebuildSDPForBookingPayload(
            booking_contract=booking_contract,
            sub_task_ids=sub_task_ids,
            assignments=assignments
        )

        # set PRIMARY CAM for all assignments
        for ass in payload.assignments:
            ass.service_role_id = 2

        response = client.post(
            client.app.url_path_for('rebuild_sdp_for_booking', booking_contract=booking_contract),
            json=jsonable_encoder(payload, custom_encoder={Decimal: str}))

        assert response.status_code == 200


    @mock.patch('api.v2.services.external.prefect_v3_flow_service.PrefectV3APIMixin._emit_api_event')
    @pytest.mark.parametrize("booking_contract, dc_engagement_id, buying_program_type_id, sub_task_ids,"
                             "service_type_id, dc_user_ids",
                             [
                                 (-999999999699, 94, 5, [114, 115], 2, [5, 888, 884]),
                             ])
    def test_rebuild_sdp_for_booking_with_new_shares(
            self, emit_api_event_mock, db_session: GetSessionDep,
            client: TestClient,booking_contract:int, dc_engagement_id: int,
            buying_program_type_id:int, sub_task_ids: list[int],
            service_type_id: int, dc_user_ids: list[int], assignments: list[V2BookingEngagementAssignment],
                                     prepare_booking_contract):
        """
        Tests the 'rebuild_sdp_for_booking' endpoint with new engagement shares.

        This test verifies that the API correctly handles a scenario where a user who doesn't have
        an existing mapping to an engagement is included in the assignments. The system should
        create a new engagement share and trigger an event to handle this new relationship.

        Given:
        - A booking contract is pre-configured in the database.
        - Valid sub_task_ids and assignment list.
        - The first user's relationship with the engagement is explicitly removed from the database.

        Action:
        - Delete the CAM-to-engagement mapping for the first user.
        - POST the payload to the rebuild_sdp_for_booking endpoint, which includes this user.

        Assertion:
        - The HTTP response code is 200 (OK), indicating success.
        - A Prefect flow event is emitted exactly once..
        - A Prefect flow event is emitted with the correct parameters to set up the new engagement share.
        """

        # remove cam to engagement mapping for the first user
        first_user = dc_user_ids[0]
        stmt = text("""
           DELETE FROM DC_CAM_TO_ENGAGEMENT
            WHERE user_id = :user_id
              AND dc_engagement_id = :dc_engagement_id
        """).bindparams(user_id=first_user, dc_engagement_id=dc_engagement_id)

        db_session.exec(stmt)
        db_session.commit()

        logger.info(assignments)

        payload = V2RebuildSDPForBookingPayload(
            booking_contract=booking_contract,
            sub_task_ids=sub_task_ids,
            assignments=assignments
        )

        response = client.post(
            client.app.url_path_for('rebuild_sdp_for_booking', booking_contract=booking_contract),
            json=jsonable_encoder(payload, custom_encoder={Decimal: str}))

        assert response.status_code == 200
        emit_api_event_mock.assert_called_once(), "Expected one Prefect flow event to be emitted"
        emit_api_event_mock.assert_called_with(
            'datacanvas.engagement.share.requested',
                {'prefect.resource.id': f'datacanvas.dev.engagement.{dc_engagement_id}',
                 'prefect.resource.name': 'Data Canvas Dev',
                },
                {'dc_engagement_id': dc_engagement_id,
                 'dc_user_id': mock.ANY,
                 'env': 'dev',
                 'notification_id': mock.ANY,
                 'request_id': mock.ANY,
                 'shared_with_dc_user_id': first_user,
                }
        ), f"Unexpected arguments in Prefect flow event: {emit_api_event_mock.call_args_list}"
