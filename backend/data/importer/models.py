"""
SQLAlchemy ORM 模型，映射到 anime_tracker 数据库表。
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Integer, String, Text, Date, DateTime,
    SmallInteger, DECIMAL, Boolean, ForeignKey, UniqueConstraint, func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Subject(Base):
    __tablename__ = "subject"
    __table_args__ = {"comment": "条目表（动漫）"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    bangumi_id: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    name_cn: Mapped[Optional[str]] = mapped_column(String(255))
    summary: Mapped[Optional[str]] = mapped_column(Text)
    type: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=2)
    eps: Mapped[Optional[int]] = mapped_column(Integer)
    volumes: Mapped[Optional[int]] = mapped_column(Integer)
    air_date: Mapped[Optional[date]] = mapped_column(Date)
    air_weekday: Mapped[Optional[int]] = mapped_column(SmallInteger)
    image: Mapped[Optional[str]] = mapped_column(String(512))
    score: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(3, 1))
    rank: Mapped[Optional[int]] = mapped_column(Integer)
    collection_total: Mapped[Optional[int]] = mapped_column(Integer)
    nsfw: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    import_status: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    last_imported_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )

    episodes = relationship("Episode", back_populates="subject", cascade="all, delete-orphan")
    tags = relationship("SubjectTag", back_populates="subject", cascade="all, delete-orphan")


class Episode(Base):
    __tablename__ = "episode"
    __table_args__ = {"comment": "剧集表"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    subject_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("subject.id", ondelete="CASCADE"), nullable=False
    )
    bangumi_ep_id: Mapped[Optional[int]] = mapped_column(Integer)
    type: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    sort: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(5, 1))
    name: Mapped[Optional[str]] = mapped_column(String(255))
    name_cn: Mapped[Optional[str]] = mapped_column(String(255))
    duration: Mapped[Optional[str]] = mapped_column(String(16))
    airdate: Mapped[Optional[date]] = mapped_column(Date)
    description: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(4), nullable=False, default="NA")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp()
    )

    subject = relationship("Subject", back_populates="episodes")


class SubjectTag(Base):
    __tablename__ = "subject_tag"
    __table_args__ = (
        UniqueConstraint("subject_id", "name"),
        {"comment": "条目-标签关联表"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    subject_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("subject.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(32), nullable=False)
    count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    subject = relationship("Subject", back_populates="tags")


class ImportRecord(Base):
    __tablename__ = "import_record"
    __table_args__ = {"comment": "导入记录表"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    mode: Mapped[str] = mapped_column(String(16), nullable=False)
    season_key: Mapped[Optional[str]] = mapped_column(String(32))
    started_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp()
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="RUNNING")
    subject_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp()
    )
