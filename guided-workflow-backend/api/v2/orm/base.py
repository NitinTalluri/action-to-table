import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, registry

v2_mapper_registry = registry()
V2Base = v2_mapper_registry.generate_base()

if TYPE_CHECKING:
    from sqlmodel import Session

    from api.v2.models import Model


class V2MetadataBase(V2Base):
    __abstract__ = True
    created_by: Mapped[str] = mapped_column(String(255))
    create_dtm: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=func.now(), server_default=func.now()
    )
    updated_by: Mapped[str | None] = mapped_column(String(255), default=None)
    update_dtm: Mapped[datetime.datetime | None] = mapped_column(
        DateTime, default=None, onupdate=func.now()
    )
    is_deleted: Mapped[str] = mapped_column(String, default="F", server_default="F")

    @classmethod
    def create_from_model(cls, model: "Model", logged_user: str, session: "Session"):
        model = cls(
            **model.dict(),
            created_by=logged_user,
        )
        session.add(model)
        session.commit()
        session.refresh(model)
        return model

    def update_from_model(self, model: "Model", logged_user: str, session: "Session"):
        for field, value in model.dict(
            exclude_unset=True, exclude={"create_dtm", "update_dtm"}
        ).items():
            setattr(self, field, value)
        self.updated_by = logged_user
        self.is_deleted = "F"
        session.add(self)
        session.commit()
        session.refresh(self)
        return self

    def soft_delete(self, logged_user: str, session: "Session"):
        self.is_deleted = "T"
        self.updated_by = logged_user
        session.commit()
        session.refresh(self)
        return self
