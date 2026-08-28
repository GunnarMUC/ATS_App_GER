from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _utcnow() -> datetime:
    return datetime.now(UTC)


class ReferenceCV(Base):
    __tablename__ = "reference_cvs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    original_filename: Mapped[str] = mapped_column(String(512), nullable=False)
    stored_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    media_type: Mapped[str] = mapped_column(String(32), nullable=False)
    raw_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    structured_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    ats_structural_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    fact_locks: Mapped[list[FactLock]] = relationship(back_populates="reference_cv")


class FactLock(Base):
    __tablename__ = "fact_locks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    reference_cv_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("reference_cvs.id"), nullable=False
    )
    facts_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    confirmed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    reference_cv: Mapped[ReferenceCV] = relationship(back_populates="fact_locks")


class RoleProfile(Base):
    __tablename__ = "role_profiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    role_family: Mapped[str] = mapped_column(String(64), nullable=False)
    lens_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )


class JobDescription(Base):
    __tablename__ = "job_descriptions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    title_raw: Mapped[str] = mapped_column(String(512), nullable=False, default="")
    source: Mapped[str] = mapped_column(String(32), nullable=False)
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    stored_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    language: Mapped[str] = mapped_column(String(8), nullable=False, default="de")
    analysis_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    generating: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class RoleDetection(Base):
    __tablename__ = "role_detections"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    job_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("job_descriptions.id"), nullable=False
    )
    detection_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    user_role_family: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class AdaptationPlan(Base):
    __tablename__ = "adaptation_plans"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    job_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("job_descriptions.id"), nullable=False
    )
    fact_lock_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("fact_locks.id"), nullable=False
    )
    role_profile_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("role_profiles.id"), nullable=True
    )
    plan_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft")
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class GeneratedDocument(Base):
    __tablename__ = "generated_documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    type: Mapped[str] = mapped_column(String(16), nullable=False)
    job_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("job_descriptions.id"), nullable=False
    )
    fact_lock_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("fact_locks.id"), nullable=False
    )
    plan_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("adaptation_plans.id"), nullable=False
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    structured_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    docx_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    pdf_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    txt_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    fact_guard_passed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class AppSettings(Base):
    __tablename__ = "app_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ollama_host: Mapped[str] = mapped_column(String(512), nullable=False)
    model_fast: Mapped[str] = mapped_column(String(256), nullable=False)
    model_strong: Mapped[str] = mapped_column(String(256), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )
