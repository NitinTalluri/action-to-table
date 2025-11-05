from sqlalchemy import Column, Integer, String, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import V2Base, V2MetadataBase

v2_organizational_hierarchy = Table(
    "organizational_hierarchy",
    V2Base.metadata,
    Column("mgr_title", String(255), nullable=True),
    Column("mgr_emial", String(60), nullable=True),
    Column("mgr_name", String(360), nullable=True),
    Column("emp_cco_id", String(50), nullable=True),
    Column("emp_email", String(60), nullable=True),
    Column("emp_country", String(3), nullable=True),
    Column("emp_title", String(255), nullable=True),
    Column("emp_name", String(360), nullable=True),
    Column("dc_theater", String(500), nullable=True),
    Column("emp_cco_id_masked", String(50), nullable=True),
    Column("level1_cisco_worker_name", String(360), nullable=True),
    Column("level2_cisco_worker_name", String(360), nullable=True),
    Column("level3_cisco_worker_name", String(360), nullable=True),
    Column("level4_cisco_worker_name", String(360), nullable=True),
    Column("level5_cisco_worker_name", String(360), nullable=True),
    Column("level6_cisco_worker_name", String(360), nullable=True),
    Column("level7_cisco_worker_name", String(360), nullable=True),
    Column("level8_cisco_worker_name", String(360), nullable=True),
    Column("level9_cisco_worker_name", String(360), nullable=True),
    Column("level10_cisco_worker_name", String(360), nullable=True),
    Column("level11_cisco_worker_name", String(360), nullable=True),
    Column("level12_cisco_worker_name", String(360), nullable=True),
    Column("level13_cisco_worker_name", String(360), nullable=True),
    Column("level14_cisco_worker_name", String(360), nullable=True),
)


class V2User(V2MetadataBase):
    __tablename__ = "dc_users"
    user_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cisco_cco_id: Mapped[str] = mapped_column(String(255), nullable=False)
    user_title: Mapped[str] = mapped_column(String(255), nullable=False)
    engagements = relationship("V2CamEngagement", back_populates="user")


__all__ = ["V2User", "v2_organizational_hierarchy"]
