from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))

    branch: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    cgpa: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    telegram_user_id: Mapped[Optional[str]] = mapped_column(
        String(100), unique=True, nullable=True
    )
    telegram_alerts_enabled: Mapped[bool] = mapped_column(
        Boolean, default=False
    )

    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    skills = relationship(
        "UserSkill", back_populates="user", cascade="all, delete-orphan"
    )
    preferences = relationship(
        "UserPreference",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    recommendations = relationship(
        "Recommendation",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    actions = relationship(
        "UserJobAction",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    survey_responses = relationship(
        "SurveyResponse",
        back_populates="user",
        cascade="all, delete-orphan",
    )


class UserSkill(Base):
    __tablename__ = "user_skills"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    skill: Mapped[str] = mapped_column(String(100), index=True)

    user = relationship("User", back_populates="skills")

    __table_args__ = (
        UniqueConstraint("user_id", "skill", name="uq_user_skill"),
    )


class UserPreference(Base):
    __tablename__ = "user_preferences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), unique=True, index=True
    )

    roles: Mapped[str] = mapped_column(Text, default="")
    locations: Mapped[str] = mapped_column(Text, default="")
    work_mode: Mapped[str] = mapped_column(String(30), default="any")
    min_compensation: Mapped[float] = mapped_column(Float, default=0)

    user = relationship("User", back_populates="preferences")


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(255), index=True)
    company: Mapped[str] = mapped_column(String(255), index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    location: Mapped[str] = mapped_column(String(255), default="", index=True)
    work_mode: Mapped[str] = mapped_column(String(30), default="onsite", index=True)
    role_type: Mapped[str] = mapped_column(String(100), default="internship", index=True)

    compensation: Mapped[float] = mapped_column(Float, default=0)
    compensation_period: Mapped[str] = mapped_column(
        String(30), default="monthly"
    )

    min_cgpa: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    eligible_branches: Mapped[str] = mapped_column(Text, default="")
    eligible_years: Mapped[str] = mapped_column(Text, default="")

    apply_url: Mapped[str] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(100), default="manual", index=True)
    external_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    posted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    deadline: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)

    skills = relationship(
        "JobSkill", back_populates="job", cascade="all, delete-orphan"
    )
    recommendations = relationship(
        "Recommendation", back_populates="job", cascade="all, delete-orphan"
    )
    actions = relationship(
        "UserJobAction", back_populates="job", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint(
            "source",
            "external_id",
            name="uq_job_source_external_id",
        ),
    )


class JobSkill(Base):
    __tablename__ = "job_skills"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id"), index=True)
    skill: Mapped[str] = mapped_column(String(100), index=True)

    job = relationship("Job", back_populates="skills")

    __table_args__ = (
        UniqueConstraint("job_id", "skill", name="uq_job_skill"),
    )


class Recommendation(Base):
    __tablename__ = "recommendations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id"), index=True)

    score: Mapped[float] = mapped_column(Float)
    explanation: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    user = relationship("User", back_populates="recommendations")
    job = relationship("Job", back_populates="recommendations")

    __table_args__ = (
        UniqueConstraint("user_id", "job_id", name="uq_recommendation"),
    )


class UserJobAction(Base):
    __tablename__ = "user_job_actions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id"), index=True)

    action: Mapped[str] = mapped_column(String(50), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    user = relationship("User", back_populates="actions")
    job = relationship("Job", back_populates="actions")


class SurveyResponse(Base):
    __tablename__ = "survey_responses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id"), nullable=True, index=True
    )

    helped_find_relevant: Mapped[str] = mapped_column(String(30))
    applied_more: Mapped[str] = mapped_column(String(30))
    comments: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    user = relationship("User", back_populates="survey_responses")
