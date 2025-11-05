from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from . import V2MetadataBase


class V2FileManagement(V2MetadataBase):
    __tablename__ = "dc_file_management_liveboards"
    liveboard_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    display_name: Mapped[str] = mapped_column(String(255))
    liveboard_type: Mapped[str] = mapped_column(String(255))
    location: Mapped[str] = mapped_column(String(255))
    is_deleted: Mapped[str] = mapped_column(String(255), default="F")
    liveboard_type_value: Mapped[str] = mapped_column(String(255))
    liveboard_name: Mapped[str] = mapped_column(String(255))
    guid: Mapped[str] = mapped_column(String(255))
    canvas_id: Mapped[int] = mapped_column(Integer)
    canvas_import_status: Mapped[str] = mapped_column(String(255))
