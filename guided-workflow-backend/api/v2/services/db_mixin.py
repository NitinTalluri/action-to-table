from typing import TYPE_CHECKING, Optional, Type

from .exceptions import ServiceException

if TYPE_CHECKING:
    from sqlmodel import Session


class SessionMixin:
    def __init__(self, session: "Session"):
        self._session = session
        self._has_context = False

    def __enter__(self):
        self._has_context = True
        return self

    def __exit__(
        self, exc_type: Optional[Type[Exception]], exc_val: Optional[Exception], exc_tb
    ):
        self._has_context = False
        if exc_type is None:
            self._session.commit()
        else:
            self._session.rollback()

    @property
    def session(self):
        if not self._has_context:
            raise ServiceException(
                "SessionMixin must be used as a context manager", 500
            )
        return self._session
