from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, DateTime, Integer, String, text
from sqlalchemy.sql.elements import BindParameter
from starlette.status import HTTP_404_NOT_FOUND

from . import ServiceException, SessionMixin

if TYPE_CHECKING:
    from sqlmodel import Session

    from api.v2.models import (
        UserSDPCompletionDeliverablePayload,
        UserSDPCompletionDeliverableResponse,
    )
    from api.v2.orm import V2User


class UserSdpService(SessionMixin):
    """
    Service class for enforcing business logic and ddl operations
    """

    def __init__(self, session: "Session"):
        super().__init__(session)

    def _check_completion_fks(
        self,
        sub_task_id: int,
        booking_contract: int,
        completion_type_id: int,
        dc_engagement_id: int,
        due_date: date,
    ) -> None:
        from api.v2.queries import make_completion_fk_membership_query

        query = make_completion_fk_membership_query(
            sub_task_id=sub_task_id,
            booking_contract=booking_contract,
            dc_engagement_id=dc_engagement_id,
            completion_type_id=completion_type_id,
        )

        missing_fks = self.session.exec(query).all()
        if missing_fks:
            msgs = [f"{row.type} : {row.id} is missing" for row in missing_fks]
            raise ServiceException(code=HTTP_404_NOT_FOUND, msg=", ".join(msgs))

    def get_completion(
        self,
        sub_task_id: int,
        booking_contract: int,
        dc_user_id: int,
        cycle_iterator: int,
        dc_engagement_id: int,
        due_date: date,
    ) -> "UserSDPCompletionDeliverableResponse":
        """
        Query a completion. Since we allow for 'uncompleting' a completion, we don't use the
        typical 'is_deleted' column to filter.
        """
        from api.v2.models import UserSDPCompletionDeliverableResponse
        from api.v2.orm import SDPTaskCompletion

        stmt = (
            text(
                """
            SELECT
             SUB_TASK_ID, BOOKING_CONTRACT, DC_USER_ID, CYCLE_ITERATOR,
                         COMPLETION_TYPE_ID, DC_ENGAGEMENT_ID, CREATED_BY, CREATE_DTM, UPDATED_BY, UPDATE_DTM,
                         IS_DELETED = 'F' AS IS_COMPLETED, NOTE, DUE_DATE
            FROM IDENTIFIER(:table_name)
            WHERE SUB_TASK_ID = :sub_task_id AND BOOKING_CONTRACT = :booking_contract AND DC_USER_ID = :dc_user_id
            AND CYCLE_ITERATOR = :cycle_iterator AND DC_ENGAGEMENT_ID = :dc_engagement_id AND DUE_DATE = :due_date
            """
            )
            .bindparams(
                table_name=SDPTaskCompletion.__tablename__,
                sub_task_id=sub_task_id,
                booking_contract=booking_contract,
                dc_user_id=dc_user_id,
                cycle_iterator=cycle_iterator,
                dc_engagement_id=dc_engagement_id,
                due_date=due_date,
            )
            .columns(
                sub_task_id=Integer,
                booking_contract=Integer,
                dc_user_id=Integer,
                cycle_iterator=Integer,
                completion_type_id=Integer,
                dc_engagement_id=Integer,
                created_by=String,
                create_dtm=DateTime,
                updated_by=String,
                update_dtm=DateTime,
                is_completed=Boolean,
                note=String,
                due_date=Date,
            )
        )

        result = self.session.exec(stmt).one_or_none()
        if result is None:
            msg = f"Completion not found for sub_task_id: {sub_task_id}, booking_contract: {booking_contract}, dc_user_id: {dc_user_id}, cycle_iterator: {cycle_iterator}, dc_engagement_id: {dc_engagement_id}, due_date: {due_date}"
            raise ServiceException(code=HTTP_404_NOT_FOUND, msg=msg)

        return UserSDPCompletionDeliverableResponse.from_orm(result)

    def process_completion(
        self, payload: "UserSDPCompletionDeliverablePayload", requestor: "V2User"
    ) -> None:
        """
        Process a completion payload
        """

        from api.v2.orm import SDPTaskCompletion

        self._check_completion_fks(
            sub_task_id=payload.sub_task_id,
            booking_contract=payload.booking_contract,
            completion_type_id=payload.completion_type_id,
            dc_engagement_id=payload.dc_engagement_id,
            due_date=payload.due_date,
        )

        stmt = text(
            # language=Snowflake
            """
            MERGE INTO IDENTIFIER(:table_name) AS target
            USING (
                VALUES (:sub_task_id, :booking_contract, :dc_user_id, :cycle_iterator, :completion_type_id,
                        :dc_engagement_id, :due_date, :created_by, :is_completed, :note) AS
                    source (sub_task_id, booking_contract, dc_user_id, cycle_iterator, completion_type_id,
                            dc_engagement_id, due_date, created_by, is_completed, note)
            )
              ON target.sub_task_id = source.sub_task_id
              AND target.booking_contract = source.booking_contract
              AND target.cycle_iterator = source.cycle_iterator
              AND target.dc_engagement_id = source.dc_engagement_id
              AND target.due_date = source.due_date
            WHEN MATCHED AND (target.is_deleted = 'F' AND NOT source.is_completed ) THEN
                -- Marking previously completed as uncompleted
                UPDATE SET is_deleted='T', updated_by = source.created_by, update_dtm = SYSDATE(), dc_user_id = source.dc_user_id
            WHEN MATCHED AND (target.is_deleted = 'T' AND source.is_completed ) THEN
                -- Completing previously uncompleted
                UPDATE SET is_deleted='F', updated_by = source.created_by, update_dtm = SYSDATE(), dc_user_id = source.dc_user_id, completion_type_id = source.completion_type_id, note = source.note
            WHEN NOT MATCHED THEN
                INSERT (SUB_TASK_ID, BOOKING_CONTRACT, DC_USER_ID, CYCLE_ITERATOR,
                         COMPLETION_TYPE_ID, DC_ENGAGEMENT_ID, DUE_DATE, CREATED_BY, CREATE_DTM, IS_DELETED, NOTE)
                VALUES (source.sub_task_id, source.booking_contract, source.dc_user_id, source.cycle_iterator,
                        NVL(source.completion_type_id, 1), source.dc_engagement_id, source.due_date,
                        source.created_by, SYSDATE(), 'F', source.note)
            ;
                """
        ).bindparams(
            BindParameter(
                "table_name", type_=String, value=SDPTaskCompletion.__tablename__
            ),
            BindParameter("sub_task_id", type_=Integer, value=payload.sub_task_id),
            BindParameter(
                "booking_contract", type_=Integer, value=payload.booking_contract
            ),
            BindParameter("dc_user_id", type_=Integer, value=requestor.user_id),
            BindParameter(
                "cycle_iterator", type_=Integer, value=payload.cycle_iterator
            ),
            BindParameter(
                "completion_type_id", type_=Integer, value=payload.completion_type_id
            ),
            BindParameter(
                "dc_engagement_id", type_=Integer, value=payload.dc_engagement_id
            ),
            BindParameter("due_date", type_=Date, value=payload.due_date),
            BindParameter("created_by", type_=String, value=requestor.cisco_cco_id),
            BindParameter("is_completed", type_=Boolean, value=payload.is_completed),
            BindParameter("note", type_=String, value=payload.note),
        )

        self.session.execute(stmt)
