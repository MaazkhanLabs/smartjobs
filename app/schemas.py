from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class UserSignup(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: str
    password: str = Field(min_length=6)
    branch: Optional[str] = None
    year: Optional[int] = Field(default=None, ge=1, le=10)
    cgpa: Optional[float] = Field(default=None, ge=0, le=10)


class UserLogin(BaseModel):
    email: str
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
    email: str
    branch: Optional[str]
    year: Optional[int]
    cgpa: Optional[float]
