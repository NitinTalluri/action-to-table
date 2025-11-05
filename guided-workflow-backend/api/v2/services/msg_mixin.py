from functools import partial
from typing import TYPE_CHECKING, Callable, Protocol

if TYPE_CHECKING:
    from sqlalchemy import Engine
    from sqlmodel import Session

    from api.v2 import ExternalServiceTracker
    from api.v2.models import NotificationCategory


class LogMsgFn(Protocol):
    def __call__(self, msg: str) -> None: ...


class ExitStatusFn(Protocol):
    def __call__(self, *, msg: str | None = None) -> None: ...


MsgPartials = tuple[LogMsgFn, ExitStatusFn, ExitStatusFn]


class MsgMixin:
    def log_msg(
        self,
        msg: str,
        notification_id: int,
        ext_tracker: "ExternalServiceTracker",
        session: "Session",
    ):
        from api.v2.models import TextMessageCreate

        data_msgs = [
            TextMessageCreate(
                type="text",
                data=msg,
            )
        ]
        stmt = ext_tracker.make_message_append_statement(notification_id, data_msgs)
        session.exec(stmt)
        session.commit()

    def update_status(
        self,
        notification_id: int,
        ext_tracker: "ExternalServiceTracker",
        session: "Session",
        status: "NotificationCategory",
        cisco_cco_id: str,
        msg: str | None = None,
    ):
        stmt = ext_tracker.make_update_notification_status_statement(
            notification_id=notification_id,
            status=status,
            updated_by=cisco_cco_id,
        )
        session.exec(stmt)
        if msg is not None:
            from api.v2.models import TextMessageCreate

            data_msgs = [
                TextMessageCreate(
                    type="text",
                    data=msg,
                )
            ]
            stmt_log = ext_tracker.make_message_append_statement(
                notification_id, data_msgs
            )
            session.exec(stmt_log)
        session.commit()

    def make_msg_partial(
        self,
        notification_id: int,
        ext_tracker: "ExternalServiceTracker",
        session: "Session",
        cisco_cco_id: str,
    ) -> MsgPartials:
        from api.v2.models import NotificationCategory

        log_msg: Callable[[str], None] = partial(
            self.log_msg,
            notification_id=notification_id,
            ext_tracker=ext_tracker,
            session=session,
        )
        exit_error: Callable[[str | None], None] = partial(
            self.update_status,
            notification_id=notification_id,
            ext_tracker=ext_tracker,
            session=session,
            status=NotificationCategory.ERROR,
            cisco_cco_id=cisco_cco_id,
        )
        exit_success: Callable[[str | None], None] = partial(
            self.update_status,
            notification_id=notification_id,
            ext_tracker=ext_tracker,
            session=session,
            status=NotificationCategory.RESULT,
            cisco_cco_id=cisco_cco_id,
        )
        return log_msg, exit_error, exit_success


class EngineCompatMsgMixin:
    def __init__(self, engine: "Engine"):
        self.engine = engine

    def log_msg(
        self,
        msg: str,
        notification_id: int,
        ext_tracker: "ExternalServiceTracker",
    ):
        from api.v2.models import TextMessageCreate

        data_msgs = [
            TextMessageCreate(
                type="text",
                data=msg,
            )
        ]
        stmt = ext_tracker.make_message_append_statement(notification_id, data_msgs)
        with self.engine.begin() as conn:
            conn.execute(stmt)

    def update_status(
        self,
        notification_id: int,
        ext_tracker: "ExternalServiceTracker",
        status: "NotificationCategory",
        cisco_cco_id: str,
        msg: str | None = None,
    ):
        stmt = ext_tracker.make_update_notification_status_statement(
            notification_id=notification_id,
            status=status,
            updated_by=cisco_cco_id,
        )
        with self.engine.begin() as conn:
            conn.execute(stmt)

            if msg is not None:
                from api.v2.models import TextMessageCreate

                data_msgs = [
                    TextMessageCreate(
                        type="text",
                        data=msg,
                    )
                ]
                stmt_log = ext_tracker.make_message_append_statement(
                    notification_id, data_msgs
                )
                conn.execute(stmt_log)

    def make_msg_partial(
        self,
        notification_id: int,
        ext_tracker: "ExternalServiceTracker",
        cisco_cco_id: str,
    ) -> MsgPartials:
        from api.v2.models import NotificationCategory

        log_msg: Callable[[str], None] = partial(
            self.log_msg,
            notification_id=notification_id,
            ext_tracker=ext_tracker,
        )
        exit_error: Callable[[str | None], None] = partial(
            self.update_status,
            notification_id=notification_id,
            ext_tracker=ext_tracker,
            status=NotificationCategory.ERROR,
            cisco_cco_id=cisco_cco_id,
        )
        exit_success: Callable[[str | None], None] = partial(
            self.update_status,
            notification_id=notification_id,
            ext_tracker=ext_tracker,
            status=NotificationCategory.RESULT,
            cisco_cco_id=cisco_cco_id,
        )
        return log_msg, exit_error, exit_success


__all__ = [
    "EngineCompatMsgMixin",
    "MsgMixin",
    "MsgPartials",
]
