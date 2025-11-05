from api.v2.queries.stored_proc import make_stored_proc_statement, parse_stored_proc_result
import pytest
from sqlalchemy import text
import json
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
logger.addHandler(handler)

@pytest.mark.parametrize("booking_contract, buying_program_type_id,"
                         "sub_task_ids, sub_tasks_filter_enabled,"
                         "expected_return_code",
                         [
                             (-999999999699, -1, None, False, 304),
                             (-999999999699, 5, None, False, 304),
                             (-999999999699, 2, None, False, 200),
                             (-999999999699, 2, [92, 93], False, 422),
                             (-999999999699, 5, [92, 93], True, 200),
                        ])
def test_dc_sdp_contract_changes(db_session,
                                 booking_contract: int,
                                 buying_program_type_id: int,
                                 sub_task_ids: list[int] | None,
                                 sub_tasks_filter_enabled: bool,
                                 expected_return_code: int):

    # set buying_program type_id for the booking contract.
    stmt = text("""
       UPDATE dc_bookings_contracts
          SET buying_program_type_id = :buying_program_type_id,
              agreement_end_date = CURRENT_DATE() 
        WHERE booking_contract = :booking_contract
        """).bindparams(buying_program_type_id=buying_program_type_id, booking_contract=booking_contract)
    db_session.exec(stmt)
    db_session.commit()
    logger.info("Updated booking_contract=%s with buying_program_type_id=%s and agreement_end_date=CURRENT_DATE", booking_contract, buying_program_type_id)

   # call the stored procedure
    proc_name= "dc_sdp_contract_changes"
    params:dict = {'booking_contract': booking_contract}
    if sub_task_ids:
        params['sub_task_ids'] = sub_task_ids

    logger.info(f'{params=}')
    stmt = make_stored_proc_statement(has_params=True
    ).bindparams(
        proc_name=proc_name,
        params=json.dumps(params, separators=(",", ":")),
    )

    db_session.begin()
    raw_result = db_session.exec(stmt).scalar()
    db_session.commit()
    parsed_result = parse_stored_proc_result(raw_result)
    logger.info(parsed_result)

    assert parsed_result.get("code") == expected_return_code

    # if SDP was run, ensure only necessary sub_tasks were added
    if expected_return_code == 200 and sub_task_ids:
        stmt = text("""
            SELECT BOOLAND_AGG(SUB_TASK_ID IN (:sub_task_ids))
              FROM dc_deliverables_core_eng
             WHERE booking_contract = :booking_contract
        """).bindparams(booking_contract=booking_contract, sub_task_ids=sub_task_ids)

        result = db_session.exec(stmt).scalar()
        assert result is sub_tasks_filter_enabled


