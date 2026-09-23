# Smart Internship & Job Aggregator — Complete Implementation Specification

## 0. Goal

Build a minimal but working final-year project called **Smart Internship & Job Aggregator for College Students**.

The application must:

- Collect internship/job postings from:
  - manually entered jobs
  - plain-text college email messages
  - Telegram-channel messages (adapter/skeleton)
  - selected company career pages (HTML scraper skeleton)
- Let students maintain:
  - name/email/password
  - branch
  - year
  - CGPA
  - skills
  - preferred roles
  - preferred locations
  - remote/onsite preference
  - minimum stipend/salary
- Rank jobs using a transparent rule-based score from 0 to 1.
- Provide:
  - FastAPI backend
  - Jinja2 server-rendered dashboard
  - Telegram bot
  - scheduled scraping
  - daily Telegram digest
  - action/event analytics
  - simple survey
- Use PostgreSQL in production and SQLite locally.

## 1. Important implementation rules

1. Use Python 3.11+.
2. Use FastAPI + SQLAlchemy 2.x.
3. Use PostgreSQL through `DATABASE_URL`; SQLite is valid for local development.
4. Use Jinja2 templates and plain CSS. Do not add React/Vue/Next.js.
5. Passwords must be hashed. Never store plain-text passwords.
6. JWT should be stored in an HTTP-only cookie for browser authentication.
7. Do not expose secrets in source code.
8. Scrapers must be adapters with clear placeholders for real sources.
9. Respect robots.txt, terms of service, rate limits, and source permissions when adding real scrapers.
10. Job apply links should redirect to the original source; do not scrape or proxy application forms.
11. Recommendation scoring must be deterministic and explainable.
12. Duplicate jobs should be avoided using a source + external ID or normalized apply URL.
13. The project should run without any real external source by using seeded dummy jobs.

---

# 2. Project structure

```text
smart-job-aggregator/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── auth.py
│   ├── matching.py
│   ├── dependencies.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── jobs.py
│   │   ├── recommendations.py
│   │   └── analytics.py
│   ├── scrapers/
│   │   ├── __init__.py
│   │   ├── email_parser.py
│   │   ├── dummy_company.py
│   │   └── runner.py
│   ├── telegram/
│   │   ├── __init__.py
│   │   └── bot.py
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── profile.py
│   │   ├── jobs.py
│   │   ├── admin.py
│   │   ├── web.py
│   │   └── survey.py
│   ├── templates/
│   │   ├── base.html
│   │   ├── login.html
│   │   ├── signup.html
│   │   ├── dashboard.html
│   │   ├── job_detail.html
│   │   ├── profile.html
│   │   ├── survey.html
│   │   └── message.html
│   └── static/
│       └── style.css
├── scripts/
│   ├── seed.py
│   ├── compute_recommendations.py
│   └── analytics.py
├── tests/
│   ├── test_matching.py
│   └── test_auth.py
├── .env.example
├── .gitignore
├── requirements.txt
├── README.md
└── IMPLEMENTATION.md
```

---

# 3. requirements.txt

```txt
fastapi
uvicorn[standard]
sqlalchemy>=2.0
pydantic>=2.0
pydantic-settings
python-dotenv
jinja2
python-multipart
passlib[bcrypt]
python-jose[cryptography]
httpx
beautifulsoup4
apscheduler
python-telegram-bot[job-queue]
psycopg[binary]
email-validator
pytest
```

---

# 4. .env.example

```env
APP_NAME=Smart Internship Aggregator
SECRET_KEY=change-this-to-a-long-random-secret
DATABASE_URL=sqlite:///./jobs.db

# Optional admin secret used by manual admin endpoints
ADMIN_SECRET=change-admin-secret

# Telegram
TELEGRAM_BOT_TOKEN=

# SMTP
SMTP_HOST=
SMTP_PORT=587
SMTP_USERNAME=
SMTP_PASSWORD=
SMTP_FROM=

# Application URL
BASE_URL=http://127.0.0.1:8000

# Scheduler
ENABLE_SCHEDULER=true
ENABLE_TELEGRAM_BOT=false
```

---

# 5. .gitignore

```gitignore
__pycache__/
*.py[cod]
.pytest_cache/
.venv/
venv/
.env
*.db
*.sqlite3
.idea/
.vscode/
.DS_Store
```

---

# 6. app/config.py

```python
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Smart Internship Aggregator"
    secret_key: str = "change-me"
    database_url: str = "sqlite:///./jobs.db"

    admin_secret: str = "change-admin-secret"

    telegram_bot_token: str = ""
    base_url: str = "http://127.0.0.1:8000"

    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from: str = ""

    enable_scheduler: bool = True
    enable_telegram_bot: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
```

---

# 7. app/database.py

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings


class Base(DeclarativeBase):
    pass


connect_args = {}
if settings.database_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.database_url,
    connect_args=connect_args,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

---

# 8. app/models.py

```python
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
    location: Mapped[str] = mapped_column(String(255), default="")
    work_mode: Mapped[str] = mapped_column(String(30), default="onsite")
    role_type: Mapped[str] = mapped_column(String(100), default="internship")

    compensation: Mapped[float] = mapped_column(Float, default=0)
    compensation_period: Mapped[str] = mapped_column(
        String(30), default="monthly"
    )

    min_cgpa: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    eligible_branches: Mapped[str] = mapped_column(Text, default="")
    eligible_years: Mapped[str] = mapped_column(Text, default="")

    apply_url: Mapped[str] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(100), default="manual")
    external_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    posted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    deadline: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

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
```

---

# 9. app/schemas.py

```python
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserSignup(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=6)
    branch: Optional[str] = None
    year: Optional[int] = Field(default=None, ge=1, le=10)
    cgpa: Optional[float] = Field(default=None, ge=0, le=10)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserProfileUpdate(BaseModel):
    name: Optional[str] = None
    branch: Optional[str] = None
    year: Optional[int] = Field(default=None, ge=1, le=10)
    cgpa: Optional[float] = Field(default=None, ge=0, le=10)


class PreferencesUpdate(BaseModel):
    roles: list[str] = []
    locations: list[str] = []
    work_mode: str = "any"
    min_compensation: float = Field(default=0, ge=0)


class SkillsUpdate(BaseModel):
    skills: list[str] = []


class JobCreate(BaseModel):
    title: str
    company: str
    description: str = ""
    location: str = ""
    work_mode: str = "onsite"
    role_type: str = "internship"
    compensation: float = 0
    compensation_period: str = "monthly"
    min_cgpa: Optional[float] = None
    eligible_branches: list[str] = []
    eligible_years: list[int] = []
    skills: list[str] = []
    apply_url: str
    source: str = "manual"
    external_id: Optional[str] = None


class ActionCreate(BaseModel):
    action: str


class SurveyCreate(BaseModel):
    helped_find_relevant: str
    applied_more: str
    comments: str = ""


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: EmailStr
    branch: Optional[str]
    year: Optional[int]
    cgpa: Optional[float]
```

---

# 10. app/auth.py

```python
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings


ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def create_access_token(user_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {
        "sub": str(user_id),
        "exp": expire,
    }
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def decode_access_token(token: str) -> int | None:
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[ALGORITHM],
        )
        user_id = payload.get("sub")
        if user_id is None:
            return None
        return int(user_id)
    except (JWTError, ValueError, TypeError):
        return None
```

---

# 11. app/dependencies.py

```python
from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import decode_access_token
from app.database import get_db
from app.models import User


def get_current_user(
    access_token: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
) -> User:
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Login required",
        )

    user_id = decode_access_token(access_token)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session",
        )

    user = db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return user
```

---

# 12. app/matching.py

This is the core transparent matching algorithm.

```python
from app.models import Job, User


def csv_values(value: str | None) -> set[str]:
    if not value:
        return set()

    return {
        item.strip().lower()
        for item in value.split(",")
        if item.strip()
    }


def normalized_values(values: list[str]) -> set[str]:
    return {
        value.strip().lower()
        for value in values
        if value and value.strip()
    }


def calculate_match(user: User, job: Job) -> tuple[float, str]:
    """
    Transparent 0-1 recommendation score.

    Components:
      1. Eligibility: 0.40
      2. Skill overlap: 0.30
      3. Role preference: 0.10
      4. Location/work-mode preference: 0.10
      5. Compensation preference: 0.10

    Eligibility is treated as a gate:
      - If CGPA is below required CGPA -> score 0
      - If branch is explicitly restricted and does not match -> score 0
      - If year is explicitly restricted and does not match -> score 0

    For eligible users:
      final score =
        0.40 * eligibility_score
        + 0.30 * skill_score
        + 0.10 * role_score
        + 0.10 * preference_score
        + 0.10 * compensation_score

    The explanation returned with the recommendation makes the result
    understandable to the student.
    """

    reasons: list[str] = []

    # -----------------------------
    # 1. Hard eligibility
    # -----------------------------
    if job.min_cgpa is not None:
        if user.cgpa is None:
            return 0.0, "CGPA is required for this opportunity."
        if user.cgpa < job.min_cgpa:
            return 0.0, f"CGPA {user.cgpa:.2f} is below required {job.min_cgpa:.2f}."

    allowed_branches = csv_values(job.eligible_branches)
    if allowed_branches and user.branch:
        if user.branch.lower().strip() not in allowed_branches:
            return 0.0, "Your branch is not listed as eligible."

    allowed_years = csv_values(job.eligible_years)
    if allowed_years and user.year is not None:
        if str(user.year) not in allowed_years:
            return 0.0, "Your academic year is not listed as eligible."

    eligibility_score = 1.0
    reasons.append("Eligible")

    # -----------------------------
    # 2. Skill overlap
    # -----------------------------
    user_skills = {skill.skill.strip().lower() for skill in user.skills}
    job_skills = {skill.skill.strip().lower() for skill in job.skills}

    if job_skills:
        matched_skills = user_skills.intersection(job_skills)
        skill_score = len(matched_skills) / len(job_skills)

        if matched_skills:
            reasons.append(
                "Skills: " + ", ".join(sorted(matched_skills))
            )
    else:
        skill_score = 0.5
        reasons.append("No structured skill requirements supplied")

    # -----------------------------
    # 3. Role preference
    # -----------------------------
    preferences = user.preferences

    preferred_roles = (
        normalized_values(preferences.roles)
        if preferences
        else set()
    )

    if preferred_roles:
        job_role_text = f"{job.title} {job.role_type}".lower()
        role_match = any(role in job_role_text for role in preferred_roles)
        role_score = 1.0 if role_match else 0.0
        if role_match:
            reasons.append("Role preference matched")
    else:
        role_score = 0.5

    # -----------------------------
    # 4. Location/work-mode
    # -----------------------------
    preferred_locations = (
        normalized_values(preferences.locations)
        if preferences
        else set()
    )
    preferred_mode = preferences.work_mode if preferences else "any"

    location_match = False
    if preferred_locations:
        job_location = job.location.lower()
        location_match = any(
            location in job_location
            for location in preferred_locations
        )

    mode_match = (
        preferred_mode == "any"
        or preferred_mode.lower() == job.work_mode.lower()
    )

    if preferred_locations or preferred_mode != "any":
        preference_score = (
            (1.0 if location_match else 0.0)
            + (1.0 if mode_match else 0.0)
        ) / (
            (1 if preferred_locations else 0)
            + (1 if preferred_mode != "any" else 0)
        )
    else:
        preference_score = 0.5

    if location_match:
        reasons.append("Location preference matched")
    if mode_match and preferred_mode != "any":
        reasons.append("Work-mode preference matched")

    # -----------------------------
    # 5. Compensation
    # -----------------------------
    minimum = preferences.min_compensation if preferences else 0

    if minimum <= 0:
        compensation_score = 0.5
    elif job.compensation >= minimum:
        compensation_score = 1.0
        reasons.append("Compensation meets minimum")
    else:
        # Partial score rather than an automatic rejection.
        compensation_score = max(0.0, job.compensation / minimum)

    score = (
        0.40 * eligibility_score
        + 0.30 * skill_score
        + 0.10 * role_score
        + 0.10 * preference_score
        + 0.10 * compensation_score
    )

    score = max(0.0, min(1.0, score))

    explanation = (
        f"Score {score:.2f}. "
        + "; ".join(reasons)
        + "."
    )

    return score, explanation
```

---

# 13. app/services/jobs.py

```python
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Job, JobSkill


def create_job(db: Session, data):
    if data.external_id:
        existing = db.scalar(
            select(Job).where(
                Job.source == data.source,
                Job.external_id == data.external_id,
            )
        )
        if existing:
            return existing

    job = Job(
        title=data.title,
        company=data.company,
        description=data.description,
        location=data.location,
        work_mode=data.work_mode,
        role_type=data.role_type,
        compensation=data.compensation,
        compensation_period=data.compensation_period,
        min_cgpa=data.min_cgpa,
        eligible_branches=",".join(data.eligible_branches),
        eligible_years=",".join(map(str, data.eligible_years)),
        apply_url=data.apply_url,
        source=data.source,
        external_id=data.external_id,
    )

    db.add(job)
    db.flush()

    for skill in data.skills:
        normalized = skill.strip().lower()
        if normalized:
            db.add(JobSkill(job_id=job.id, skill=normalized))

    db.commit()
    db.refresh(job)

    return job
```

---

# 14. app/services/recommendations.py

```python
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.matching import calculate_match
from app.models import Job, Recommendation, User


def recompute_for_user(db: Session, user: User):
    jobs = db.scalars(
        select(Job).where(Job.is_active.is_(True))
    ).all()

    for job in jobs:
        score, explanation = calculate_match(user, job)

        existing = db.scalar(
            select(Recommendation).where(
                Recommendation.user_id == user.id,
                Recommendation.job_id == job.id,
            )
        )

        # Do not store zero-score recommendations.
        if score <= 0:
            if existing:
                db.delete(existing)
            continue

        if existing:
            existing.score = score
            existing.explanation = explanation
        else:
            db.add(
                Recommendation(
                    user_id=user.id,
                    job_id=job.id,
                    score=score,
                    explanation=explanation,
                )
            )

    db.commit()


def recompute_for_all_users(db: Session):
    users = db.scalars(select(User)).all()

    for user in users:
        recompute_for_user(db, user)


def recompute_for_new_job(db: Session, job: Job):
    users = db.scalars(select(User)).all()

    for user in users:
        score, explanation = calculate_match(user, job)

        if score <= 0:
            continue

        existing = db.scalar(
            select(Recommendation).where(
                Recommendation.user_id == user.id,
                Recommendation.job_id == job.id,
            )
        )

        if existing:
            existing.score = score
            existing.explanation = explanation
        else:
            db.add(
                Recommendation(
                    user_id=user.id,
                    job_id=job.id,
                    score=score,
                    explanation=explanation,
                )
            )

    db.commit()
```

---

# 15. app/services/analytics.py

```python
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Job, Recommendation, User, UserJobAction


def get_analytics(db: Session):
    total_users = db.scalar(
        select(func.count(User.id))
    ) or 0

    total_jobs = db.scalar(
        select(func.count(Job.id))
    ) or 0

    total_recommendations = db.scalar(
        select(func.count(Recommendation.id))
    ) or 0

    average_recommendations_per_user = (
        total_recommendations / total_users
        if total_users
        else 0
    )

    viewed = db.scalar(
        select(func.count(UserJobAction.id)).where(
            UserJobAction.action == "viewed"
        )
    ) or 0

    clicked = db.scalar(
        select(func.count(UserJobAction.id)).where(
            UserJobAction.action == "clicked_apply"
        )
    ) or 0

    applied = db.scalar(
        select(func.count(UserJobAction.id)).where(
            UserJobAction.action == "marked_applied"
        )
    ) or 0

    ctr = clicked / viewed if viewed else 0
    application_rate = applied / viewed if viewed else 0

    return {
        "total_users": total_users,
        "total_jobs": total_jobs,
        "total_recommendations": total_recommendations,
        "average_recommendations_per_user": round(
            average_recommendations_per_user, 2
        ),
        "views": viewed,
        "apply_clicks": clicked,
        "marked_applied": applied,
        "ctr": round(ctr, 4),
        "application_rate": round(application_rate, 4),
    }
```

---

# 16. app/routers/auth.py

```python
from fastapi import APIRouter, Depends, Form, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import create_access_token, hash_password, verify_password
from app.database import get_db
from app.dependencies import get_current_user
from app.models import User, UserPreference
from app.schemas import UserLogin, UserSignup

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/signup")
def signup(
    data: UserSignup,
    response: Response,
    db: Session = Depends(get_db),
):
    email = data.email.lower()

    existing = db.scalar(
        select(User).where(User.email == email)
    )
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Email already registered",
        )

    user = User(
        name=data.name,
        email=email,
        password_hash=hash_password(data.password),
        branch=data.branch,
        year=data.year,
        cgpa=data.cgpa,
    )

    db.add(user)
    db.flush()

    db.add(UserPreference(user_id=user.id))
    db.commit()
    db.refresh(user)

    token = create_access_token(user.id)

    response.set_cookie(
        "access_token",
        token,
        httponly=True,
        samesite="lax",
        secure=False,  # Set True behind HTTPS in production.
        max_age=60 * 60 * 24,
    )

    return {"message": "Account created", "user_id": user.id}


@router.post("/login")
def login(
    data: UserLogin,
    response: Response,
    db: Session = Depends(get_db),
):
    user = db.scalar(
        select(User).where(User.email == data.email.lower())
    )

    if not user or not verify_password(
        data.password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
        )

    token = create_access_token(user.id)

    response.set_cookie(
        "access_token",
        token,
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=60 * 60 * 24,
    )

    return {"message": "Logged in"}


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie("access_token")
    return {"message": "Logged out"}


@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "branch": user.branch,
        "year": user.year,
        "cgpa": user.cgpa,
    }
```

---

# 17. app/routers/profile.py

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import User, UserPreference, UserSkill
from app.schemas import PreferencesUpdate, SkillsUpdate, UserProfileUpdate
from app.services.recommendations import recompute_for_user

router = APIRouter(prefix="/api/profile", tags=["profile"])


@router.get("")
def get_profile(user: User = Depends(get_current_user)):
    preferences = user.preferences

    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "branch": user.branch,
        "year": user.year,
        "cgpa": user.cgpa,
        "skills": [skill.skill for skill in user.skills],
        "preferences": {
            "roles": preferences.roles.split(",") if preferences and preferences.roles else [],
            "locations": preferences.locations.split(",") if preferences and preferences.locations else [],
            "work_mode": preferences.work_mode if preferences else "any",
            "min_compensation": preferences.min_compensation if preferences else 0,
        },
    }


@router.put("")
def update_profile(
    data: UserProfileUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)

    recompute_for_user(db, user)

    return {"message": "Profile updated"}


@router.put("/skills")
def update_skills(
    data: SkillsUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user.skills.clear()

    for skill in data.skills:
        normalized = skill.strip().lower()
        if normalized:
            user.skills.append(UserSkill(skill=normalized))

    db.commit()
    db.refresh(user)

    recompute_for_user(db, user)

    return {"skills": [skill.skill for skill in user.skills]}


@router.put("/preferences")
def update_preferences(
    data: PreferencesUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    preferences = user.preferences

    if not preferences:
        preferences = UserPreference(user_id=user.id)
        db.add(preferences)

    preferences.roles = ",".join(
        item.strip().lower()
        for item in data.roles
        if item.strip()
    )
    preferences.locations = ",".join(
        item.strip().lower()
        for item in data.locations
        if item.strip()
    )
    preferences.work_mode = data.work_mode.lower()
    preferences.min_compensation = data.min_compensation

    db.commit()
    db.refresh(user)

    recompute_for_user(db, user)

    return {"message": "Preferences updated"}
```

---

# 18. app/routers/jobs.py

```python
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import Job, Recommendation, User, UserJobAction
from app.schemas import ActionCreate

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.get("")
def list_jobs(
    search: str | None = None,
    location: str | None = None,
    work_mode: str | None = None,
    limit: int = Query(default=50, le=200),
    db: Session = Depends(get_db),
):
    stmt = select(Job).where(Job.is_active.is_(True))

    if search:
        pattern = f"%{search.lower()}%"
        stmt = stmt.where(
            Job.title.ilike(pattern)
            | Job.company.ilike(pattern)
        )

    if location:
        stmt = stmt.where(Job.location.ilike(f"%{location}%"))

    if work_mode:
        stmt = stmt.where(Job.work_mode == work_mode.lower())

    jobs = db.scalars(
        stmt.order_by(Job.posted_at.desc()).limit(limit)
    ).all()

    return jobs


@router.get("/recommended")
def recommended_jobs(
    min_score: float = Query(default=0, ge=0, le=1),
    limit: int = Query(default=50, le=200),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = db.execute(
        select(Recommendation, Job)
        .join(Job, Recommendation.job_id == Job.id)
        .where(
            Recommendation.user_id == user.id,
            Recommendation.score >= min_score,
            Job.is_active.is_(True),
        )
        .order_by(Recommendation.score.desc())
        .limit(limit)
    ).all()

    return [
        {
            "id": job.id,
            "title": job.title,
            "company": job.company,
            "location": job.location,
            "work_mode": job.work_mode,
            "role_type": job.role_type,
            "compensation": job.compensation,
            "compensation_period": job.compensation_period,
            "apply_url": job.apply_url,
            "score": round(rec.score, 3),
            "explanation": rec.explanation,
        }
        for rec, job in rows
    ]


@router.get("/{job_id}")
def get_job(
    job_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    job = db.get(Job, job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    recommendation = db.scalar(
        select(Recommendation).where(
            Recommendation.user_id == user.id,
            Recommendation.job_id == job.id,
        )
    )

    return {
        "job": job,
        "recommendation": {
            "score": recommendation.score,
            "explanation": recommendation.explanation,
        } if recommendation else None,
    }


@router.post("/{job_id}/action")
def mark_action(
    job_id: int,
    data: ActionCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    allowed = {
        "viewed",
        "clicked_apply",
        "marked_applied",
        "not_interested",
        "saved",
    }

    if data.action not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Action must be one of: {', '.join(sorted(allowed))}",
        )

    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    db.add(
        UserJobAction(
            user_id=user.id,
            job_id=job_id,
            action=data.action,
        )
    )
    db.commit()

    return {"message": "Action recorded"}
```

---

# 19. app/routers/admin.py

```python
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import User
from app.schemas import JobCreate
from app.services.jobs import create_job
from app.services.recommendations import recompute_for_new_job

router = APIRouter(prefix="/api/admin", tags=["admin"])


def verify_admin_secret(
    x_admin_secret: str | None = Header(default=None),
):
    if x_admin_secret != settings.admin_secret:
        raise HTTPException(
            status_code=403,
            detail="Invalid admin secret",
        )


@router.post("/jobs", dependencies=[Depends(verify_admin_secret)])
def add_job(
    data: JobCreate,
    db: Session = Depends(get_db),
):
    job = create_job(db, data)

    # Create/update recommendations immediately.
    recompute_for_new_job(db, job)

    return {
        "message": "Job created",
        "job_id": job.id,
    }
```

For a larger deployment, replace the static admin secret with proper admin user roles.

---

# 20. app/routers/survey.py

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import SurveyResponse, User
from app.schemas import SurveyCreate

router = APIRouter(prefix="/api/survey", tags=["survey"])


@router.post("")
def submit_survey(
    data: SurveyCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    response = SurveyResponse(
        user_id=user.id,
        helped_find_relevant=data.helped_find_relevant,
        applied_more=data.applied_more,
        comments=data.comments,
    )

    db.add(response)
    db.commit()

    return {"message": "Survey submitted. Thank you!"}
```

---

# 21. app/routers/web.py

```python
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.dependencies import get_current_user
from app.models import User

router = APIRouter(tags=["web"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
def home(request: Request):
    return RedirectResponse("/dashboard")


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse(
        "login.html",
        {"request": request},
    )


@router.get("/signup", response_class=HTMLResponse)
def signup_page(request: Request):
    return templates.TemplateResponse(
        "signup.html",
        {"request": request},
    )


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard(
    request: Request,
    user: User = Depends(get_current_user),
):
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "user": user,
        },
    )


@router.get("/profile", response_class=HTMLResponse)
def profile_page(
    request: Request,
    user: User = Depends(get_current_user),
):
    return templates.TemplateResponse(
        "profile.html",
        {
            "request": request,
            "user": user,
        },
    )


@router.get("/jobs/{job_id}", response_class=HTMLResponse)
def job_detail_page(
    request: Request,
    job_id: int,
    user: User = Depends(get_current_user),
):
    return templates.TemplateResponse(
        "job_detail.html",
        {
            "request": request,
            "job_id": job_id,
        },
    )


@router.get("/survey", response_class=HTMLResponse)
def survey_page(
    request: Request,
    user: User = Depends(get_current_user),
):
    return templates.TemplateResponse(
        "survey.html",
        {"request": request},
    )
```

---

# 22. app/scrapers/email_parser.py

This parser assumes the college email has a predictable plain-text format.

Example:

```text
Title: Python Developer Intern
Company: ABC Technologies
Location: Mumbai
Work Mode: Hybrid
Role Type: Internship
Stipend: 12000
Minimum CGPA: 7
Eligible Branches: CS, IT
Eligible Years: 2,3
Skills: Python, FastAPI, SQL
Apply Link: https://example.com/apply/123

Description:
Build APIs and internal tools using Python.
```

Implementation:

```python
import re

from app.schemas import JobCreate


def extract(pattern: str, text: str, default: str = "") -> str:
    match = re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE)
    return match.group(1).strip() if match else default


def parse_college_email(email_text: str) -> JobCreate:
    title = extract(r"^Title:\s*(.+)$", email_text)
    company = extract(r"^Company:\s*(.+)$", email_text)
    location = extract(r"^Location:\s*(.+)$", email_text)
    work_mode = extract(r"^Work Mode:\s*(.+)$", email_text, "onsite")
    role_type = extract(r"^Role Type:\s*(.+)$", email_text, "internship")

    stipend_text = extract(r"^Stipend:\s*([0-9]+(?:\.[0-9]+)?)$", email_text, "0")
    cgpa_text = extract(
        r"^Minimum CGPA:\s*([0-9]+(?:\.[0-9]+)?)$",
        email_text,
        "",
    )

    branches = extract(r"^Eligible Branches:\s*(.+)$", email_text)
    years = extract(r"^Eligible Years:\s*(.+)$", email_text)
    skills = extract(r"^Skills:\s*(.+)$", email_text)

    apply_url = extract(r"^Apply Link:\s*(\S+)$", email_text)

    description_match = re.search(
        r"Description:\s*(.*)",
        email_text,
        flags=re.IGNORECASE | re.DOTALL,
    )

    description = (
        description_match.group(1).strip()
        if description_match
        else ""
    )

    if not title or not company or not apply_url:
        raise ValueError(
            "Email must contain Title, Company and Apply Link."
        )

    return JobCreate(
        title=title,
        company=company,
        description=description,
        location=location,
        work_mode=work_mode.lower(),
        role_type=role_type.lower(),
        compensation=float(stipend_text),
        min_cgpa=float(cgpa_text) if cgpa_text else None,
        eligible_branches=[
            item.strip() for item in branches.split(",") if item.strip()
        ],
        eligible_years=[
            int(item.strip())
            for item in years.split(",")
            if item.strip().isdigit()
        ],
        skills=[
            item.strip()
            for item in skills.split(",")
            if item.strip()
        ],
        apply_url=apply_url,
        source="college_email",
        external_id=apply_url,
    )
```

---

# 23. app/scrapers/dummy_company.py

```python
import httpx
from bs4 import BeautifulSoup

from app.schemas import JobCreate


DUMMY_URL = "https://example.com/jobs"


async def scrape_dummy_company() -> list[JobCreate]:
    """
    Skeleton only.

    Replace DUMMY_URL with a company career page that you are permitted
    to scrape. Inspect its HTML and change the CSS selectors accordingly.
    """

    async with httpx.AsyncClient(
        timeout=20,
        follow_redirects=True,
        headers={
            "User-Agent": "StudentJobAggregator/1.0"
        },
    ) as client:
        response = await client.get(DUMMY_URL)
        response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    jobs: list[JobCreate] = []

    # Example selectors. These are intentionally placeholders.
    for card in soup.select(".job-card"):
        title_node = card.select_one(".job-title")
        company_node = card.select_one(".company")
        location_node = card.select_one(".location")
        link_node = card.select_one("a")

        if not title_node or not link_node:
            continue

        apply_url = link_node.get("href")
        if not apply_url:
            continue

        jobs.append(
            JobCreate(
                title=title_node.get_text(" ", strip=True),
                company=(
                    company_node.get_text(" ", strip=True)
                    if company_node
                    else "Dummy Company"
                ),
                location=(
                    location_node.get_text(" ", strip=True)
                    if location_node
                    else ""
                ),
                description=card.get_text(" ", strip=True),
                apply_url=apply_url,
                source="dummy_company",
                external_id=apply_url,
                skills=[],
            )
        )

    return jobs
```

---

# 24. app/scrapers/runner.py

```python
import asyncio

from app.database import SessionLocal
from app.scrapers.dummy_company import scrape_dummy_company
from app.services.jobs import create_job
from app.services.recommendations import recompute_for_new_job


async def run_company_scraper():
    jobs = await scrape_dummy_company()

    db = SessionLocal()

    try:
        for data in jobs:
            job = create_job(db, data)
            recompute_for_new_job(db, job)
    finally:
        db.close()


def run_company_scraper_sync():
    asyncio.run(run_company_scraper())


def run_email_import(email_text: str):
    from app.scrapers.email_parser import parse_college_email

    data = parse_college_email(email_text)

    db = SessionLocal()

    try:
        job = create_job(db, data)
        recompute_for_new_job(db, job)
    finally:
        db.close()
```

---

# 25. app/telegram/bot.py

The bot supports:

- `/start`
- `/profile`
- `/jobs`
- `/alerts on`
- `/alerts off`

A simple account-linking flow is used:

1. Logged-in user opens `/profile`.
2. Backend generates a short one-time Telegram linking token.
3. User sends `/start LINK_TOKEN` to the bot.
4. Bot finds the user and stores `telegram_user_id`.

For the minimal implementation below, use email + token verification.

```python
import secrets

from sqlalchemy import select

from app.config import settings
from app.database import SessionLocal
from app.models import User, Recommendation, Job

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)


# In production, persist these tokens in a database table with expiry.
LINK_TOKENS: dict[str, int] = {}


def create_link_token(user_id: int) -> str:
    token = secrets.token_urlsafe(12)
    LINK_TOKENS[token] = user_id
    return token


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user:
        return

    args = context.args

    db = SessionLocal()

    try:
        if args:
            token = args[0]
            user_id = LINK_TOKENS.pop(token, None)

            if user_id:
                user = db.get(User, user_id)
                if user:
                    user.telegram_user_id = str(
                        update.effective_user.id
                    )
                    db.commit()

                    await update.message.reply_text(
                        "Telegram account linked successfully."
                    )
                    return

        await update.message.reply_text(
            "Welcome to Smart Internship Aggregator!\n\n"
            "Link your account from the web profile page, then use /jobs."
        )
    finally:
        db.close()


async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = str(update.effective_user.id)

    db = SessionLocal()

    try:
        user = db.scalar(
            select(User).where(
                User.telegram_user_id == telegram_id
            )
        )

        if not user:
            await update.message.reply_text(
                "Your Telegram account is not linked yet."
            )
            return

        skills = ", ".join(skill.skill for skill in user.skills)

        await update.message.reply_text(
            f"Name: {user.name}\n"
            f"Branch: {user.branch or '-'}\n"
            f"Year: {user.year or '-'}\n"
            f"CGPA: {user.cgpa or '-'}\n"
            f"Skills: {skills or '-'}"
        )
    finally:
        db.close()


async def jobs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = str(update.effective_user.id)

    db = SessionLocal()

    try:
        user = db.scalar(
            select(User).where(
                User.telegram_user_id == telegram_id
            )
        )

        if not user:
            await update.message.reply_text(
                "Link your Telegram account first."
            )
            return

        rows = db.execute(
            select(Recommendation, Job)
            .join(Job, Recommendation.job_id == Job.id)
            .where(
                Recommendation.user_id == user.id,
                Job.is_active.is_(True),
            )
            .order_by(Recommendation.score.desc())
            .limit(5)
        ).all()

        if not rows:
            await update.message.reply_text(
                "No recommendations yet. Complete your profile first."
            )
            return

        messages = []

        for index, (rec, job) in enumerate(rows, start=1):
            messages.append(
                f"{index}. {job.title} — {job.company}\n"
                f"Score: {rec.score:.2f}\n"
                f"{job.location} | {job.work_mode}\n"
                f"Apply: {job.apply_url}"
            )

        await update.message.reply_text(
            "\n\n".join(messages)
        )
    finally:
        db.close()


async def alerts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = str(update.effective_user.id)

    if not context.args or context.args[0].lower() not in {"on", "off"}:
        await update.message.reply_text(
            "Usage: /alerts on OR /alerts off"
        )
        return

    enabled = context.args[0].lower() == "on"

    db = SessionLocal()

    try:
        user = db.scalar(
            select(User).where(
                User.telegram_user_id == telegram_id
            )
        )

        if not user:
            await update.message.reply_text(
                "Link your account first."
            )
            return

        user.telegram_alerts_enabled = enabled
        db.commit()

        await update.message.reply_text(
            "Daily alerts enabled." if enabled
            else "Daily alerts disabled."
        )
    finally:
        db.close()


async def send_daily_digest(context: ContextTypes.DEFAULT_TYPE):
    db = SessionLocal()

    try:
        users = db.scalars(
            select(User).where(
                User.telegram_alerts_enabled.is_(True),
                User.telegram_user_id.is_not(None),
            )
        ).all()

        for user in users:
            rows = db.execute(
                select(Recommendation, Job)
                .join(Job, Recommendation.job_id == Job.id)
                .where(
                    Recommendation.user_id == user.id,
                    Job.is_active.is_(True),
                )
                .order_by(Recommendation.score.desc())
                .limit(5)
            ).all()

            if not rows:
                continue

            text = "🎯 Your top internship/job matches today:\n\n"

            for i, (rec, job) in enumerate(rows, start=1):
                text += (
                    f"{i}. {job.title} — {job.company}\n"
                    f"Match: {rec.score:.0%}\n"
                    f"{job.location} | {job.work_mode}\n"
                    f"{job.apply_url}\n\n"
                )

            try:
                await context.bot.send_message(
                    chat_id=int(user.telegram_user_id),
                    text=text,
                )
            except Exception as exc:
                print(
                    f"Telegram delivery failed for user {user.id}: {exc}"
                )
    finally:
        db.close()


def build_application():
    if not settings.telegram_bot_token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not configured.")

    application = Application.builder().token(
        settings.telegram_bot_token
    ).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("profile", profile))
    application.add_handler(CommandHandler("jobs", jobs))
    application.add_handler(CommandHandler("alerts", alerts))

    # 24-hour digest.
    application.job_queue.run_repeating(
        send_daily_digest,
        interval=24 * 60 * 60,
        first=30,
    )

    return application


def run_bot():
    application = build_application()
    application.run_polling()
```

## Telegram linking API

Add this endpoint to the profile router:

```python
from app.telegram.bot import create_link_token
from app.config import settings


@router.post("/telegram/link-token")
def telegram_link_token(
    user: User = Depends(get_current_user),
):
    token = create_link_token(user.id)

    return {
        "token": token,
        "bot_start_link": (
            f"https://t.me/YOUR_BOT_USERNAME?start={token}"
        ),
        "note": "Replace YOUR_BOT_USERNAME with your Telegram bot username.",
    }
```

For a production implementation, store linking tokens in a database table with:

- token hash
- user ID
- created_at
- expires_at
- used_at

instead of the in-memory dictionary.

---

# 26. app/main.py

```python
import asyncio
import threading
from contextlib import asynccontextmanager

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import Base, engine
from app.routers import admin, auth, jobs, profile, survey, web
from app.scrapers.runner import run_company_scraper


scheduler = BackgroundScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # For a student project, create tables automatically.
    # For production, use Alembic migrations.
    Base.metadata.create_all(bind=engine)

    if settings.enable_scheduler:
        scheduler.add_job(
            run_company_scraper,
            "interval",
            hours=4,
            id="company_scraper",
            replace_existing=True,
        )
        scheduler.start()

    # Optional Telegram process.
    if settings.enable_telegram_bot and settings.telegram_bot_token:
        from app.telegram.bot import run_bot

        thread = threading.Thread(
            target=run_bot,
            daemon=True,
        )
        thread.start()

    yield

    if scheduler.running:
        scheduler.shutdown()


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    lifespan=lifespan,
)

app.mount(
    "/static",
    StaticFiles(directory="app/static"),
    name="static",
)

app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(jobs.router)
app.include_router(admin.router)
app.include_router(survey.router)
app.include_router(web.router)


@app.get("/health")
def health():
    return {"status": "ok"}
```

---

# 27. app/routers/__init__.py

```python
# Package marker.
```

Create empty `__init__.py` files in:

```text
app/
app/services/
app/scrapers/
app/telegram/
app/routers/
```

---

# 28. app/templates/base.html

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Smart Jobs{% endblock %}</title>
    <link rel="stylesheet" href="/static/style.css">
</head>
<body>

<nav class="navbar">
    <a class="brand" href="/dashboard">SmartJobs</a>

    <div class="nav-links">
        <a href="/dashboard">Dashboard</a>
        <a href="/profile">Profile</a>
        <a href="/survey">Survey</a>
        <button onclick="logout()">Logout</button>
    </div>
</nav>

<main class="container">
    {% block content %}{% endblock %}
</main>

<script>
async function logout() {
    await fetch("/api/auth/logout", {method: "POST"});
    window.location.href = "/login";
}
</script>

{% block scripts %}{% endblock %}
</body>
</html>
```

---

# 29. app/templates/login.html

```html
{% extends "base.html" %}

{% block title %}Login — SmartJobs{% endblock %}

{% block content %}
<div class="auth-card">
    <h1>Welcome back</h1>
    <p>Find internships and jobs matched to your profile.</p>

    <form id="loginForm">
        <label>Email</label>
        <input type="email" id="email" required>

        <label>Password</label>
        <input type="password" id="password" required>

        <button class="primary" type="submit">Login</button>
    </form>

    <p id="message"></p>

    <p>
        New student?
        <a href="/signup">Create an account</a>
    </p>
</div>
{% endblock %}

{% block scripts %}
<script>
document.getElementById("loginForm").addEventListener("submit", async (event) => {
    event.preventDefault();

    const response = await fetch("/api/auth/login", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
            email: document.getElementById("email").value,
            password: document.getElementById("password").value
        })
    });

    const data = await response.json();

    if (response.ok) {
        window.location.href = "/dashboard";
    } else {
        document.getElementById("message").textContent =
            data.detail || "Login failed";
    }
});
</script>
{% endblock %}
```

---

# 30. app/templates/signup.html

```html
{% extends "base.html" %}

{% block title %}Sign up — SmartJobs{% endblock %}

{% block content %}
<div class="auth-card">
    <h1>Create student profile</h1>

    <form id="signupForm">
        <label>Name</label>
        <input id="name" required>

        <label>Email</label>
        <input id="email" type="email" required>

        <label>Password</label>
        <input id="password" type="password" minlength="6" required>

        <label>Branch</label>
        <input id="branch" placeholder="Computer Science">

        <label>Year</label>
        <input id="year" type="number" min="1" max="6">

        <label>CGPA</label>
        <input id="cgpa" type="number" min="0" max="10" step="0.01">

        <button class="primary" type="submit">Create account</button>
    </form>

    <p id="message"></p>

    <p>
        Already registered?
        <a href="/login">Login</a>
    </p>
</div>
{% endblock %}

{% block scripts %}
<script>
document.getElementById("signupForm").addEventListener("submit", async (event) => {
    event.preventDefault();

    const yearValue = document.getElementById("year").value;
    const cgpaValue = document.getElementById("cgpa").value;

    const response = await fetch("/api/auth/signup", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
            name: document.getElementById("name").value,
            email: document.getElementById("email").value,
            password: document.getElementById("password").value,
            branch: document.getElementById("branch").value || null,
            year: yearValue ? Number(yearValue) : null,
            cgpa: cgpaValue ? Number(cgpaValue) : null
        })
    });

    const data = await response.json();

    if (response.ok) {
        window.location.href = "/dashboard";
    } else {
        document.getElementById("message").textContent =
            data.detail || "Signup failed";
    }
});
</script>
{% endblock %}
```

---

# 31. app/templates/dashboard.html

```html
{% extends "base.html" %}

{% block title %}Dashboard — SmartJobs{% endblock %}

{% block content %}

<section class="hero">
    <div>
        <p class="eyebrow">Personalized career feed</p>
        <h1>Hello, {{ user.name }} 👋</h1>
        <p>
            Opportunities are ranked using your skills, eligibility,
            preferences and compensation requirements.
        </p>
    </div>
</section>

<section class="profile-summary card">
    <h2>Profile Summary</h2>

    <div class="summary-grid">
        <div>
            <strong>Branch</strong>
            <span>{{ user.branch or "Not set" }}</span>
        </div>

        <div>
            <strong>Year</strong>
            <span>{{ user.year or "Not set" }}</span>
        </div>

        <div>
            <strong>CGPA</strong>
            <span>{{ user.cgpa or "Not set" }}</span>
        </div>

        <div>
            <strong>Skills</strong>
            <span>
                {% if user.skills %}
                    {{ user.skills | map(attribute="skill") | join(", ") }}
                {% else %}
                    Add skills
                {% endif %}
            </span>
        </div>
    </div>

    <a class="button secondary" href="/profile">Edit profile</a>
</section>

<section class="filters card">
    <h2>Recommended opportunities</h2>

    <div class="filter-row">
        <input id="search" placeholder="Search role or company">
        <input id="location" placeholder="Location">
        <select id="workMode">
            <option value="">Any work mode</option>
            <option value="remote">Remote</option>
            <option value="hybrid">Hybrid</option>
            <option value="onsite">Onsite</option>
        </select>
        <button class="primary" onclick="loadJobs()">Filter</button>
    </div>
</section>

<section id="jobs" class="jobs-grid">
    <p>Loading recommendations...</p>
</section>

{% endblock %}

{% block scripts %}
<script>
async function loadJobs() {
    const search = document.getElementById("search").value;
    const location = document.getElementById("location").value;
    const workMode = document.getElementById("workMode").value;

    const params = new URLSearchParams();
    if (search) params.set("search", search);
    if (location) params.set("location", location);
    if (workMode) params.set("work_mode", workMode);

    const response = await fetch("/api/jobs/recommended?limit=50");
    const jobs = await response.json();

    const filtered = jobs.filter(job => {
        const text = `${job.title} ${job.company}`.toLowerCase();

        const searchOk =
            !search || text.includes(search.toLowerCase());

        const locationOk =
            !location ||
            job.location.toLowerCase().includes(location.toLowerCase());

        const modeOk =
            !workMode || job.work_mode === workMode;

        return searchOk && locationOk && modeOk;
    });

    const container = document.getElementById("jobs");

    if (!filtered.length) {
        container.innerHTML = `
            <div class="empty card">
                <h3>No matches found</h3>
                <p>Try changing your filters or update your profile.</p>
            </div>
        `;
        return;
    }

    container.innerHTML = filtered.map(job => `
        <article class="job-card">
            <div class="job-top">
                <span class="score">${Math.round(job.score * 100)}% match</span>
                <span class="tag">${job.role_type}</span>
            </div>

            <h3>${escapeHtml(job.title)}</h3>
            <p class="company">${escapeHtml(job.company)}</p>

            <p>
                ${escapeHtml(job.location || "Location not specified")}
                · ${escapeHtml(job.work_mode)}
            </p>

            <p class="explanation">${escapeHtml(job.explanation)}</p>

            <div class="job-actions">
                <a class="button primary"
                   href="${job.apply_url}"
                   target="_blank"
                   rel="noopener"
                   onclick="recordAction(${job.id}, 'clicked_apply')">
                   Apply
                </a>

                <a class="button secondary"
                   href="/jobs/${job.id}"
                   onclick="recordAction(${job.id}, 'viewed')">
                   Details
                </a>
            </div>
        </article>
    `).join("");
}

async function recordAction(jobId, action) {
    await fetch(`/api/jobs/${jobId}/action`, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({action})
    });
}

function escapeHtml(value) {
    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

loadJobs();
</script>
{% endblock %}
```

---

# 32. app/templates/job_detail.html

```html
{% extends "base.html" %}

{% block title %}Job details — SmartJobs{% endblock %}

{% block content %}
<div id="jobContainer" class="card">
    Loading...
</div>
{% endblock %}

{% block scripts %}
<script>
const jobId = {{ job_id }};

async function loadJob() {
    const response = await fetch(`/api/jobs/${jobId}`);
    const data = await response.json();

    if (!response.ok) {
        document.getElementById("jobContainer").innerHTML =
            "<h2>Job not found</h2>";
        return;
    }

    const job = data.job;
    const recommendation = data.recommendation;

    await recordAction("viewed");

    document.getElementById("jobContainer").innerHTML = `
        <span class="score">
            ${recommendation
                ? Math.round(recommendation.score * 100) + "% match"
                : "Not ranked"}
        </span>

        <h1>${escapeHtml(job.title)}</h1>
        <h2>${escapeHtml(job.company)}</h2>

        <p>
            ${escapeHtml(job.location)}
            · ${escapeHtml(job.work_mode)}
            · ${escapeHtml(job.role_type)}
        </p>

        <p>
            Compensation:
            ${job.compensation || 0}
            ${escapeHtml(job.compensation_period)}
        </p>

        <hr>

        <p class="job-description">
            ${escapeHtml(job.description)}
        </p>

        ${
            recommendation
            ? `<div class="explanation">
                 <strong>Why this is recommended:</strong>
                 ${escapeHtml(recommendation.explanation)}
               </div>`
            : ""
        }

        <div class="job-actions">
            <a class="button primary"
               href="${job.apply_url}"
               target="_blank"
               rel="noopener"
               onclick="recordAction('clicked_apply')">
               Apply
            </a>

            <button class="button secondary"
                    onclick="recordAction('marked_applied')">
                Mark as applied
            </button>

            <button class="button secondary"
                    onclick="recordAction('not_interested')">
                Not interested
            </button>

            <button class="button secondary"
                    onclick="recordAction('saved')">
                Save
            </button>
        </div>

        <p id="actionMessage"></p>
    `;
}

async function recordAction(action) {
    const response = await fetch(
        `/api/jobs/${jobId}/action`,
        {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({action})
        }
    );

    const data = await response.json();

    const message = document.getElementById("actionMessage");
    if (message) {
        message.textContent =
            response.ok
            ? "Action recorded."
            : (data.detail || "Could not record action.");
    }
}

function escapeHtml(value) {
    return String(value || "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

loadJob();
</script>
{% endblock %}
```

---

# 33. app/templates/profile.html

```html
{% extends "base.html" %}

{% block title %}Profile — SmartJobs{% endblock %}

{% block content %}
<div class="card">
    <h1>My profile</h1>

    <form id="profileForm">
        <label>Name</label>
        <input id="name" value="{{ user.name }}">

        <label>Branch</label>
        <input id="branch" value="{{ user.branch or '' }}">

        <label>Year</label>
        <input id="year" type="number" value="{{ user.year or '' }}">

        <label>CGPA</label>
        <input id="cgpa" type="number" step="0.01" value="{{ user.cgpa or '' }}">

        <button class="primary" type="submit">Save profile</button>
    </form>
</div>

<div class="card">
    <h2>Skills</h2>
    <p>Comma-separated: Python, SQL, JavaScript, FastAPI</p>

    <input id="skills">

    <button class="primary" onclick="saveSkills()">
        Save skills
    </button>
</div>

<div class="card">
    <h2>Preferences</h2>

    <label>Preferred roles</label>
    <input id="roles" placeholder="Python Developer, Data Analyst">

    <label>Preferred locations</label>
    <input id="locations" placeholder="Mumbai, Pune, Remote">

    <label>Work mode</label>
    <select id="workMode">
        <option value="any">Any</option>
        <option value="remote">Remote</option>
        <option value="hybrid">Hybrid</option>
        <option value="onsite">Onsite</option>
    </select>

    <label>Minimum stipend/salary</label>
    <input id="minimum" type="number" min="0">

    <button class="primary" onclick="savePreferences()">
        Save preferences
    </button>
</div>

<div class="card">
    <h2>Telegram</h2>
    <p>Link your Telegram account to receive recommendations.</p>
    <button class="primary" onclick="generateTelegramLink()">
        Generate Telegram link
    </button>
    <p id="telegramResult"></p>
</div>

<p id="message"></p>
{% endblock %}

{% block scripts %}
<script>
async function saveProfile(event) {
    event.preventDefault();

    const response = await fetch("/api/profile", {
        method: "PUT",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
            name: document.getElementById("name").value,
            branch: document.getElementById("branch").value || null,
            year: document.getElementById("year").value
                ? Number(document.getElementById("year").value)
                : null,
            cgpa: document.getElementById("cgpa").value
                ? Number(document.getElementById("cgpa").value)
                : null
        })
    });

    document.getElementById("message").textContent =
        response.ok ? "Profile saved." : "Could not save profile.";
}

async function saveSkills() {
    const skills = document.getElementById("skills").value
        .split(",")
        .map(x => x.trim())
        .filter(Boolean);

    const response = await fetch("/api/profile/skills", {
        method: "PUT",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({skills})
    });

    document.getElementById("message").textContent =
        response.ok ? "Skills saved." : "Could not save skills.";
}

async function savePreferences() {
    const roles = document.getElementById("roles").value
        .split(",")
        .map(x => x.trim())
        .filter(Boolean);

    const locations = document.getElementById("locations").value
        .split(",")
        .map(x => x.trim())
        .filter(Boolean);

    const response = await fetch("/api/profile/preferences", {
        method: "PUT",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
            roles,
            locations,
            work_mode: document.getElementById("workMode").value,
            min_compensation:
                Number(document.getElementById("minimum").value || 0)
        })
    });

    document.getElementById("message").textContent =
        response.ok ? "Preferences saved." : "Could not save preferences.";
}

async function generateTelegramLink() {
    const response = await fetch(
        "/api/profile/telegram/link-token",
        {method: "POST"}
    );

    const data = await response.json();

    if (!response.ok) {
        document.getElementById("telegramResult").textContent =
            data.detail || "Could not generate token.";
        return;
    }

    document.getElementById("telegramResult").innerHTML =
        `<a href="${data.bot_start_link}" target="_blank">
            Open Telegram and link account
         </a>`;
}

document
    .getElementById("profileForm")
    .addEventListener("submit", saveProfile);
</script>
{% endblock %}
```

---

# 34. app/templates/survey.html

```html
{% extends "base.html" %}

{% block title %}Survey — SmartJobs{% endblock %}

{% block content %}
<div class="card survey-card">
    <h1>Student feedback</h1>
    <p>Your responses help evaluate the project.</p>

    <form id="surveyForm">

        <label>Did this tool help you find more relevant opportunities?</label>
        <select id="helped">
            <option value="yes">Yes</option>
            <option value="somewhat">Somewhat</option>
            <option value="no">No</option>
        </select>

        <label>Did you apply to more roles because of this tool?</label>
        <select id="applied">
            <option value="yes">Yes</option>
            <option value="somewhat">Somewhat</option>
            <option value="no">No</option>
        </select>

        <label>Comments</label>
        <textarea id="comments" rows="5"></textarea>

        <button class="primary" type="submit">
            Submit survey
        </button>
    </form>

    <p id="message"></p>
</div>
{% endblock %}

{% block scripts %}
<script>
document.getElementById("surveyForm").addEventListener("submit", async (event) => {
    event.preventDefault();

    const response = await fetch("/api/survey", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
            helped_find_relevant:
                document.getElementById("helped").value,
            applied_more:
                document.getElementById("applied").value,
            comments:
                document.getElementById("comments").value
        })
    });

    const data = await response.json();

    document.getElementById("message").textContent =
        data.message || "Submitted";
});
</script>
{% endblock %}
```

---

# 35. app/templates/message.html

```html
{% extends "base.html" %}

{% block content %}
<div class="card">
    <h1>{{ title }}</h1>
    <p>{{ message }}</p>
</div>
{% endblock %}
```

---

# 36. app/static/style.css

```css
* {
    box-sizing: border-box;
}

body {
    margin: 0;
    font-family: Arial, sans-serif;
    background: #f5f7fb;
    color: #172033;
}

a {
    color: inherit;
}

.navbar {
    height: 64px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0 6%;
    background: white;
    border-bottom: 1px solid #e5e7eb;
}

.brand {
    text-decoration: none;
    font-weight: 800;
    font-size: 22px;
}

.nav-links {
    display: flex;
    gap: 18px;
    align-items: center;
}

.nav-links a {
    text-decoration: none;
}

.nav-links button {
    border: 0;
    background: transparent;
    cursor: pointer;
}

.container {
    width: min(1100px, 92%);
    margin: 32px auto;
}

.hero {
    padding: 32px;
    background: linear-gradient(135deg, #e8efff, #ffffff);
    border-radius: 20px;
    margin-bottom: 24px;
}

.eyebrow {
    text-transform: uppercase;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 1px;
}

.card,
.job-card,
.auth-card {
    background: white;
    border: 1px solid #e6e8ee;
    border-radius: 16px;
    padding: 24px;
    box-shadow: 0 6px 24px rgba(0, 0, 0, 0.04);
    margin-bottom: 20px;
}

.auth-card {
    max-width: 460px;
    margin: 70px auto;
}

.summary-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 16px;
    margin-bottom: 20px;
}

.summary-grid div {
    padding: 16px;
    background: #f8fafc;
    border-radius: 12px;
}

.summary-grid strong,
.summary-grid span {
    display: block;
}

.summary-grid span {
    margin-top: 8px;
}

.filter-row {
    display: grid;
    grid-template-columns: 2fr 1fr 1fr auto;
    gap: 10px;
}

input,
select,
textarea {
    width: 100%;
    padding: 12px;
    border: 1px solid #d6dae3;
    border-radius: 9px;
    margin: 6px 0 14px;
    font: inherit;
}

label {
    display: block;
    font-weight: 600;
    margin-top: 10px;
}

button,
.button {
    border: 0;
    border-radius: 9px;
    padding: 11px 16px;
    cursor: pointer;
    text-decoration: none;
    display: inline-block;
}

.primary {
    background: #1d4ed8;
    color: white;
}

.secondary {
    background: #eef2ff;
    color: #1e3a8a;
}

.jobs-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 18px;
}

.job-card {
    margin: 0;
}

.job-top {
    display: flex;
    justify-content: space-between;
    gap: 10px;
}

.score {
    display: inline-block;
    background: #dcfce7;
    color: #166534;
    padding: 6px 10px;
    border-radius: 999px;
    font-size: 13px;
    font-weight: 700;
}

.tag {
    background: #f1f5f9;
    padding: 6px 10px;
    border-radius: 999px;
    font-size: 12px;
}

.company {
    font-weight: 700;
}

.explanation {
    color: #475569;
    font-size: 14px;
    background: #f8fafc;
    padding: 12px;
    border-radius: 9px;
}

.job-actions {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
    margin-top: 18px;
}

.job-description {
    line-height: 1.7;
    white-space: pre-wrap;
}

hr {
    border: 0;
    border-top: 1px solid #e5e7eb;
    margin: 24px 0;
}

@media (max-width: 800px) {
    .summary-grid,
    .jobs-grid,
    .filter-row {
        grid-template-columns: 1fr;
    }

    .navbar {
        padding: 0 4%;
    }

    .nav-links {
        gap: 8px;
    }
}
```

---

# 37. scripts/seed.py

```python
from app.database import Base, SessionLocal, engine
from app.models import Job, JobSkill, User, UserPreference
from app.auth import hash_password


def seed():
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        user = db.query(User).filter(
            User.email == "student@example.com"
        ).first()

        if not user:
            user = User(
                name="Demo Student",
                email="student@example.com",
                password_hash=hash_password("password123"),
                branch="Computer Science",
                year=3,
                cgpa=8.2,
            )
            db.add(user)
            db.flush()

            user.preferences = UserPreference(
                roles="python developer,data analyst",
                locations="mumbai,remote",
                work_mode="any",
                min_compensation=8000,
            )

            from app.models import UserSkill

            for skill in [
                "python",
                "sql",
                "fastapi",
                "git",
                "javascript",
            ]:
                db.add(
                    UserSkill(
                        user_id=user.id,
                        skill=skill,
                    )
                )

        if db.query(Job).count() == 0:
            jobs = [
                Job(
                    title="Python Backend Intern",
                    company="ABC Technologies",
                    description=(
                        "Build APIs and internal tools using Python and FastAPI."
                    ),
                    location="Mumbai",
                    work_mode="hybrid",
                    role_type="internship",
                    compensation=12000,
                    min_cgpa=7.0,
                    eligible_branches="Computer Science,IT",
                    eligible_years="2,3,4",
                    apply_url="https://example.com/python-intern",
                    source="seed",
                    external_id="seed-python-1",
                ),
                Job(
                    title="Frontend Developer Intern",
                    company="Demo Web Labs",
                    description="Build responsive web applications.",
                    location="Pune",
                    work_mode="onsite",
                    role_type="internship",
                    compensation=10000,
                    min_cgpa=6.5,
                    eligible_branches="Computer Science,IT",
                    eligible_years="2,3,4",
                    apply_url="https://example.com/frontend-intern",
                    source="seed",
                    external_id="seed-frontend-1",
                ),
                Job(
                    title="Data Analyst Intern",
                    company="Insight Corp",
                    description="Analyze datasets and build reports.",
                    location="Remote",
                    work_mode="remote",
                    role_type="internship",
                    compensation=15000,
                    min_cgpa=7.5,
                    eligible_branches="Computer Science,IT,Data Science",
                    eligible_years="2,3,4",
                    apply_url="https://example.com/data-analyst",
                    source="seed",
                    external_id="seed-data-1",
                ),
            ]

            db.add_all(jobs)
            db.flush()

            skills = {
                "Python Backend Intern": ["python", "fastapi", "sql", "git"],
                "Frontend Developer Intern": ["javascript", "html", "css"],
                "Data Analyst Intern": ["python", "sql", "pandas"],
            }

            for job in jobs:
                for skill in skills.get(job.title, []):
                    db.add(
                        JobSkill(
                            job_id=job.id,
                            skill=skill,
                        )
                    )

        db.commit()

        # Compute recommendations after all seed data exists.
        from app.services.recommendations import recompute_for_all_users

        recompute_for_all_users(db)

        print("Seed complete.")
        print("Demo login: student@example.com / password123")

    finally:
        db.close()


if __name__ == "__main__":
    seed()
```

---

# 38. scripts/compute_recommendations.py

```python
from app.database import SessionLocal
from app.services.recommendations import recompute_for_all_users


def main():
    db = SessionLocal()

    try:
        recompute_for_all_users(db)
        print("Recommendations recomputed for all users.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
```

Run:

```bash
python -m scripts.compute_recommendations
```

---

# 39. scripts/analytics.py

```python
import json

from app.database import SessionLocal
from app.services.analytics import get_analytics


def main():
    db = SessionLocal()

    try:
        print(
            json.dumps(
                get_analytics(db),
                indent=2,
            )
        )
    finally:
        db.close()


if __name__ == "__main__":
    main()
```

Run:

```bash
python -m scripts.analytics
```

---

# 40. Analytics interpretation

The application records:

- `viewed`
- `clicked_apply`
- `marked_applied`
- `not_interested`
- `saved`

Basic metrics:

```text
CTR = clicked_apply / viewed

Application Rate = marked_applied / viewed
```

For the final-year research report, also calculate weekly unique students:

```text
Relevant opportunities seen per student per week
=
number of distinct recommended jobs with viewed action
grouped by student and calendar week
```

A stronger version should use distinct `(user_id, job_id)` pairs instead of raw event count to avoid double counting repeated views.

---

# 41. Weekly analytics query

Add this later to `app/services/analytics.py`:

```python
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select


def weekly_relevance_stats(db):
    seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)

    rows = db.execute(
        select(
            UserJobAction.user_id,
            func.count(
                func.distinct(UserJobAction.job_id)
            ).label("relevant_jobs_seen"),
        )
        .where(
            UserJobAction.action == "viewed",
            UserJobAction.created_at >= seven_days_ago,
        )
        .group_by(UserJobAction.user_id)
    ).all()

    return [
        {
            "user_id": user_id,
            "relevant_opportunities_seen": count,
        }
        for user_id, count in rows
    ]
```

---

# 42. tests/test_matching.py

```python
from types import SimpleNamespace

from app.matching import calculate_match


def test_matching_returns_high_score_for_matching_student():
    user = SimpleNamespace(
        branch="Computer Science",
        year=3,
        cgpa=8.5,
        skills=[
            SimpleNamespace(skill="python"),
            SimpleNamespace(skill="sql"),
        ],
        preferences=SimpleNamespace(
            roles=["python developer"],
            locations=["mumbai"],
            work_mode="hybrid",
            min_compensation=8000,
        ),
    )

    job = SimpleNamespace(
        min_cgpa=7.0,
        eligible_branches="Computer Science,IT",
        eligible_years="2,3,4",
        skills=[
            SimpleNamespace(skill="python"),
            SimpleNamespace(skill="sql"),
        ],
        title="Python Developer Intern",
        role_type="internship",
        location="Mumbai",
        work_mode="hybrid",
        compensation=12000,
    )

    score, explanation = calculate_match(user, job)

    assert score > 0.7
    assert "Eligible" in explanation


def test_ineligible_cgpa_gets_zero():
    user = SimpleNamespace(
        branch="Computer Science",
        year=3,
        cgpa=5.5,
        skills=[],
        preferences=SimpleNamespace(
            roles=[],
            locations=[],
            work_mode="any",
            min_compensation=0,
        ),
    )

    job = SimpleNamespace(
        min_cgpa=7.0,
        eligible_branches="Computer Science",
        eligible_years="3",
        skills=[],
        title="Developer",
        role_type="internship",
        location="Mumbai",
        work_mode="onsite",
        compensation=10000,
    )

    score, _ = calculate_match(user, job)

    assert score == 0
```

---

# 43. tests/test_auth.py

```python
from app.auth import hash_password, verify_password


def test_password_hashing():
    password = "password123"

    hashed = hash_password(password)

    assert hashed != password
    assert verify_password(password, hashed)
    assert not verify_password("wrong-password", hashed)
```

---

# 44. Running locally

## Step 1 — create environment

Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
```

Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

## Step 2 — install dependencies

```bash
pip install -r requirements.txt
```

## Step 3 — create `.env`

Copy:

```text
.env.example
```

to:

```text
.env
```

At minimum:

```env
SECRET_KEY=some-long-random-string
DATABASE_URL=sqlite:///./jobs.db
ADMIN_SECRET=my-admin-secret
ENABLE_SCHEDULER=true
ENABLE_TELEGRAM_BOT=false
```

## Step 4 — create seed data

```bash
python -m scripts.seed
```

## Step 5 — start API

```bash
uvicorn app.main:app --reload
```

Open:

```text
http://127.0.0.1:8000
```

Swagger:

```text
http://127.0.0.1:8000/docs
```

Demo account:

```text
Email: student@example.com
Password: password123
```

---

# 45. Adding a job manually

Use Swagger or curl.

Example:

```bash
curl -X POST http://127.0.0.1:8000/api/admin/jobs \
  -H "Content-Type: application/json" \
  -H "X-Admin-Secret: my-admin-secret" \
  -d '{
    "title": "Python Developer Intern",
    "company": "Example Company",
    "description": "Work on backend APIs.",
    "location": "Mumbai",
    "work_mode": "hybrid",
    "role_type": "internship",
    "compensation": 15000,
    "compensation_period": "monthly",
    "min_cgpa": 7,
    "eligible_branches": ["Computer Science", "IT"],
    "eligible_years": [2, 3, 4],
    "skills": ["Python", "FastAPI", "SQL"],
    "apply_url": "https://example.com/apply",
    "source": "manual",
    "external_id": "example-001"
  }'
```

When the job is inserted, recommendations are calculated for all users.

---

# 46. Real email integration

For the final project, there are two possible stages.

## Stage A — easiest

Manually copy plain-text email content into:

```python
parse_college_email(email_text)
```

This proves the email ingestion pipeline.

## Stage B — actual mailbox

Use Python's `imaplib` or a provider API to:

1. Connect to the college/job-alert mailbox.
2. Read unread messages.
3. Extract plain-text body.
4. Call `parse_college_email()`.
5. Insert the resulting job.
6. Mark the email as processed.

Do not put email passwords in source code.

Environment variables:

```env
SMTP_HOST=
SMTP_PORT=587
SMTP_USERNAME=
SMTP_PASSWORD=
SMTP_FROM=
```

Note: SMTP is for sending mail. Reading incoming mail normally requires IMAP or a provider API.

---

# 47. Real Telegram channel ingestion

For the final project, treat Telegram ingestion as a separate adapter.

Possible architecture:

```text
Telegram Channel
      ↓
Telegram client/listener
      ↓
message text
      ↓
parser
      ↓
JobCreate
      ↓
create_job()
      ↓
recommendations
```

Do not assume that every Telegram channel can be scraped. Use a Telegram API/client approach only where you have permission and access.

The parser should eventually recognize:

```text
Title
Company
Role
Location
Stipend
Eligibility
Skills
Apply link
Deadline
```

Start with a fixed format so the project remains reliable.

---

# 48. Real company career page scraper

Do not scrape arbitrary websites blindly.

For each permitted company source, create an adapter:

```text
app/scrapers/
    company_a.py
    company_b.py
    company_c.py
```

Each adapter should expose:

```python
async def scrape() -> list[JobCreate]:
    ...
```

Recommended fields:

```text
title
company
description
location
work_mode
role_type
compensation
min_cgpa
eligible_branches
eligible_years
skills
apply_url
source
external_id
```

Always:

- respect robots.txt and site rules
- use reasonable request timeouts
- use a descriptive User-Agent
- rate-limit requests
- cache when possible
- avoid unnecessary repeated requests

---

# 49. APScheduler architecture

Current schedule:

```text
Every 4 hours
     ↓
company scraper
     ↓
normalize jobs
     ↓
deduplicate
     ↓
insert jobs
     ↓
calculate recommendations
```

Recommended production schedule:

```text
08:00 — college email ingestion
09:00 — company scraper
13:00 — Telegram ingestion
17:00 — company scraper
20:00 — daily recommendation refresh
21:00 — Telegram digest
```

Do not run multiple scheduler instances in a multi-worker deployment unless the scheduler is separated into its own process.

For a larger deployment:

```text
FastAPI web service
        +
Dedicated scheduler worker
        +
Telegram bot worker
```

---

# 50. Database design

Relationships:

```text
users
  |
  +---- user_skills
  |
  +---- user_preferences
  |
  +---- recommendations ---- jobs ---- job_skills
  |
  +---- user_job_actions ---- jobs
  |
  +---- survey_responses
```

Main purpose of each table:

### users

Stores student identity and academic eligibility.

### user_skills

One row per user skill.

Example:

```text
user_id | skill
1       | python
1       | sql
1       | fastapi
```

### user_preferences

Stores comma-separated preferences for the minimal implementation.

For a larger version, normalize roles and locations into separate tables.

### jobs

Stores normalized opportunity information independent of its source.

### job_skills

Stores skills required by an opportunity.

### recommendations

Materialized ranking result for fast dashboard loading.

### user_job_actions

Event log for measuring student engagement.

### survey_responses

Stores research-study feedback.

---

# 51. Recommended research metrics

For the final-year project, calculate at least:

## System metrics

- number of sources
- number of jobs collected
- duplicate jobs removed
- average jobs collected per day
- scraper success rate

## Matching metrics

- average recommendation score
- percentage of jobs passing eligibility
- average skills overlap
- top matching skill

## User metrics

- weekly active students
- opportunities viewed per student/week
- apply clicks/student/week
- applications/student/week
- CTR
- application rate

## Survey metrics

Question 1:

```text
Did this tool help you find more relevant opportunities?
```

Question 2:

```text
Did you apply to more roles because of this tool?
```

Calculate:

```text
% Yes
% Somewhat
% No
```

---

# 52. Important analytics improvement

Raw action counts can be misleading.

For example, if a student opens the same job five times:

```text
viewed = 5
```

That does not necessarily mean five different relevant opportunities.

Therefore report both:

### Event-level views

```text
total viewed events
```

and:

### Unique opportunities seen

```text
COUNT(DISTINCT job_id)
```

per student/week.

This distinction makes the research evaluation stronger.

---

# 53. Recommendation explanation shown to students

Every recommendation should explain itself.

Example:

```text
Score 0.86. Eligible; Skills: fastapi, python, sql;
Role preference matched; Location preference matched;
Work-mode preference matched; Compensation meets minimum.
```

This is an important final-year-project feature because it makes the ranking explainable instead of presenting a mysterious "AI score."

---

# 54. Suggested dashboard sections

Use this layout:

```text
------------------------------------------------
SmartJobs                         Dashboard Profile
------------------------------------------------

Hello, Maaz 👋

Your Profile
-----------------------------------------------
Branch       Year       CGPA       Skills
CS           3          8.2        Python, SQL...

[Edit Profile]

Recommended Jobs
-----------------------------------------------

[Search] [Location] [Work mode] [Filter]

┌─────────────────────────────────────────────┐
│ Python Backend Intern             92% match │
│ ABC Technologies                           │
│ Mumbai · Hybrid                            │
│                                             │
│ Skills: Python, FastAPI, SQL               │
│ Eligible · Location matched                │
│                                             │
│ [Apply] [Details]                          │
└─────────────────────────────────────────────┘
```

---

# 55. Final-year-project novelty

Do not present this as simply "a job portal."

The research/project contribution should be:

```text
Multiple fragmented opportunity sources
                ↓
        Data normalization
                ↓
       Eligibility filtering
                ↓
Transparent personalized ranking
                ↓
 Web + Telegram delivery
                ↓
    Behavioral analytics
                ↓
        Student survey
```

The central problem is **opportunity fragmentation and relevance**, not job posting itself.

---

# 56. Suggested final-year research question

A good research question:

> Does a transparent, profile-based opportunity aggregation and ranking system help college students discover more relevant internships and increase application activity compared with manually browsing fragmented job sources?

Possible hypotheses:

### H1

Students using the aggregator see more relevant opportunities per week.

### H2

Students using personalized ranking have a higher application rate.

### H3

Students report that transparent explanations increase trust in recommendations.

---

# 57. Evaluation experiment

If possible, conduct a small study with students.

Example:

```text
Participants: 20–50 students

Week 1:
Normal/manual job searching

Week 2:
Use Smart Internship Aggregator

Measure:
- relevant opportunities seen
- apply clicks
- applications
- survey responses
```

If a controlled experiment is not possible, use a before/after study and clearly state the limitation.

---

# 58. Production improvements after MVP

Do not implement these before the MVP works.

After the basic version works, consider:

1. Alembic database migrations.
2. PostgreSQL full-text search.
3. Redis + Celery/RQ for background jobs.
4. Proper OAuth login.
5. Database-backed Telegram link tokens.
6. Source-specific parsers.
7. Job deduplication using normalized URL + title/company similarity.
8. Pagination.
9. Admin dashboard.
10. Email alerts.
11. Saved jobs table.
12. Notification preferences.
13. Job expiration handling.
14. Rate limiting.
15. CSRF protection for browser forms.
16. HTTPS-only secure cookies.
17. Structured logging.
18. Monitoring.

---

# 59. Security checklist

Before deployment:

```text
[ ] Change SECRET_KEY
[ ] Change ADMIN_SECRET
[ ] Use HTTPS
[ ] Set secure=True for auth cookies
[ ] Never commit .env
[ ] Never commit Telegram bot token
[ ] Never commit SMTP password
[ ] Validate external URLs
[ ] Rate-limit login
[ ] Add CSRF protection if using cookie-authenticated state-changing forms
[ ] Use PostgreSQL backups
[ ] Add proper admin authentication
[ ] Add expiry to Telegram linking tokens
```

---

# 60. Deployment on Render/Railway

Use a PostgreSQL database.

Set:

```env
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST:5432/DATABASE
SECRET_KEY=long-random-secret
ADMIN_SECRET=long-random-admin-secret
BASE_URL=https://your-domain.example
TELEGRAM_BOT_TOKEN=...
ENABLE_SCHEDULER=true
ENABLE_TELEGRAM_BOT=false
```

Web start command:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Recommended deployment architecture:

```text
Web Service
    |
    +-- FastAPI
    +-- Jinja2
    +-- PostgreSQL

Worker / second service
    |
    +-- Telegram bot

Scheduler worker
    |
    +-- Scrapers
    +-- Recommendation updates
```

For a small college project, a single service can be used initially, but background processes should eventually be separated.

---

# 61. End-to-end workflow

## Student signup

```text
Student
 ↓
/signup
 ↓
User record
 ↓
Default preferences
 ↓
Login cookie
 ↓
Dashboard
```

## Profile update

```text
Student updates:
  skills
  CGPA
  branch
  year
  roles
  locations
  work mode
  minimum compensation

        ↓

Recommendation engine recalculates
```

## New job

```text
Email / Telegram / Website / Admin
              ↓
           Parser
              ↓
          JobCreate
              ↓
       Deduplication
              ↓
           jobs
              ↓
      job_skills
              ↓
   calculate_match(user, job)
              ↓
      recommendations
```

## Student interaction

```text
Dashboard
   ↓
viewed
   ↓
Details
   ↓
clicked_apply
   ↓
external application website
   ↓
student returns
   ↓
marked_applied
```

## Telegram

```text
/student profile
      ↓
generate link token
      ↓
Telegram /start TOKEN
      ↓
telegram_user_id linked
      ↓
/jobs
      ↓
top 5 recommendations
```

## Daily digest

```text
Scheduler
   ↓
find users with alerts enabled
   ↓
top 5 recommendations/user
   ↓
Telegram
```

---

# 62. Minimum implementation order

Tell the coding AI to implement in this order:

### Phase 1 — Backend foundation

1. Create project structure.
2. Install requirements.
3. Create config.
4. Create database.
5. Create models.
6. Create schemas.
7. Create authentication.
8. Create `/health`.

### Phase 2 — Profile

9. Signup/login/logout.
10. Profile endpoint.
11. Skills endpoint.
12. Preferences endpoint.

### Phase 3 — Jobs

13. Job model.
14. Admin job creation.
15. Job list.
16. Job details.
17. Action logging.

### Phase 4 — Matching

18. Implement `calculate_match`.
19. Unit-test scoring.
20. Compute recommendations.
21. Recompute when profile changes.
22. Recompute when job is added.

### Phase 5 — Web UI

23. Login.
24. Signup.
25. Dashboard.
26. Filters.
27. Job detail.
28. Apply tracking.
29. Profile.
30. Survey.

### Phase 6 — Sources

31. Email parser.
32. Dummy website scraper.
33. Scheduler.
34. Deduplication.

### Phase 7 — Telegram

35. Bot.
36. Account linking.
37. `/profile`.
38. `/jobs`.
39. `/alerts`.
40. Daily digest.

### Phase 8 — Research

41. Analytics.
42. Weekly metrics.
43. Survey analysis.
44. Seed dataset.
45. Testing.
46. Deployment.

---

# 63. Acceptance criteria

The implementation is complete when all of the following work:

## Authentication

```text
POST /api/auth/signup
POST /api/auth/login
POST /api/auth/logout
GET  /api/auth/me
```

## Profile

```text
GET /api/profile
PUT /api/profile
PUT /api/profile/skills
PUT /api/profile/preferences
POST /api/profile/telegram/link-token
```

## Jobs

```text
GET  /api/jobs
GET  /api/jobs/recommended
GET  /api/jobs/{job_id}
POST /api/jobs/{job_id}/action
```

## Admin

```text
POST /api/admin/jobs
```

## Survey

```text
POST /api/survey
```

## UI

```text
/login
/signup
/dashboard
/profile
/jobs/{id}
/survey
```

## Telegram

```text
/start
/profile
/jobs
/alerts on
/alerts off
```

## Research

```text
python -m scripts.analytics
```

must output at least:

```json
{
  "total_users": 1,
  "total_jobs": 3,
  "average_recommendations_per_user": 2.0,
  "views": 0,
  "apply_clicks": 0,
  "marked_applied": 0,
  "ctr": 0,
  "application_rate": 0
}
```

---

# 64. Final instruction to the coding AI

Implement this project as a **working MVP**, not as a collection of disconnected examples.

Before finishing:

1. Ensure all imports resolve.
2. Ensure `Base.metadata.create_all()` creates all tables.
3. Run the seed script.
4. Start FastAPI.
5. Verify signup/login.
6. Verify the demo account.
7. Verify recommendations appear.
8. Verify filters.
9. Verify job actions are stored.
10. Verify survey submission.
11. Verify analytics.
12. Verify admin job insertion.
13. Verify that adding a job creates recommendations.
14. Verify scraper functions fail gracefully when the dummy source is unavailable.
15. Verify Telegram is optional when no token is configured.
16. Do not require React.
17. Do not add unnecessary AI/ML dependencies.
18. Keep the matching algorithm deterministic and explainable.
19. Add comments where a student needs to replace dummy source selectors.
20. Keep secrets in `.env`.
21. Use dummy sources until the real sources are explicitly configured.

The first milestone should run entirely with:

```bash
pip install -r requirements.txt
python -m scripts.seed
uvicorn app.main:app --reload
```

and should provide a usable student dashboard without requiring Telegram, SMTP, PostgreSQL, or any real scraper.
